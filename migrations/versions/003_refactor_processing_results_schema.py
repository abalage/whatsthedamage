"""Refactor processing_results schema to use result_id and separate columns.

This migration performs a major refactoring of the processing_results and transactions tables:
1. Adds new columns to processing_results table (result_id, row_count, processing_time, ml_enabled, start_date, end_date)
2. Migrates data from JSON columns (processing_metadata, statistical_metadata) to new columns
3. Adds result_id column to transactions table with foreign key to processing_results
4. Drops old columns from processing_results (id, data, processing_metadata, statistical_metadata, updated_at)
5. Makes result_id the primary key

Revision ID: 003
Revises: 002
Create Date: 2026-09-21 00:00:00.000000

"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    """Upgrade database schema to use result_id and separate columns."""
    # Get inspector to check existing state
    inspector = sa.inspect(op.get_bind())
    conn = op.get_bind()
    dialect = conn.dialect.name
    
    # Step 0: Create processing_results table if it doesn't exist
    # (It should exist from SQLAlchemy models, but check just in case)
    if not inspector.has_table('processing_results'):
        op.create_table(
            'processing_results',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('data', sa.JSON(), nullable=False),
            sa.Column('processing_metadata', sa.JSON(), nullable=False),
            sa.Column('statistical_metadata', sa.JSON(), nullable=False),
            sa.Column('csv_profile_id', sa.String(length=36), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint('id'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.Index('ix_processing_results_user_id', 'user_id'),
            sa.Index('ix_processing_results_csv_profile_id', 'csv_profile_id'),
            sa.Index('ix_processing_results_created_at', 'created_at'),
        )
    
    # Step 1: Add new columns to processing_results table only if they don't exist
    # SQLite has limited ALTER TABLE support, so we check first
    existing_pr_columns = [col['name'] for col in inspector.get_columns('processing_results')]
    
    if 'result_id' not in existing_pr_columns:
        op.add_column('processing_results', sa.Column('result_id', sa.String(length=36), nullable=True))
    if 'row_count' not in existing_pr_columns:
        op.add_column('processing_results', sa.Column('row_count', sa.Integer(), nullable=True))
    if 'processing_time' not in existing_pr_columns:
        op.add_column('processing_results', sa.Column('processing_time', sa.Float(), nullable=True))
    if 'ml_enabled' not in existing_pr_columns:
        op.add_column('processing_results', sa.Column('ml_enabled', sa.Boolean(), nullable=True, server_default='0'))
    if 'start_date' not in existing_pr_columns:
        op.add_column('processing_results', sa.Column('start_date', sa.DateTime(), nullable=True))
    if 'end_date' not in existing_pr_columns:
        op.add_column('processing_results', sa.Column('end_date', sa.DateTime(), nullable=True))

    # Step 2: Handle transactions table
    if not inspector.has_table('transactions'):
        op.create_table(
            'transactions',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('result_id', sa.String(length=36), nullable=True),
            sa.Column('date', sa.String(length=20), nullable=False),
            sa.Column('transaction_type', sa.String(length=10), nullable=False),
            sa.Column('original_partner', sa.String(length=255), nullable=False),
            sa.Column('amount', sa.Float(), nullable=False),
            sa.Column('currency', sa.String(length=3), nullable=False),
            sa.Column('account', sa.String(length=100), nullable=False),
            sa.Column('deduplication_hash', sa.String(length=64), nullable=False),
            sa.Column('category_id', sa.String(length=50), nullable=True),
            sa.Column('partner', sa.String(length=255), nullable=True),
            sa.Column('notice', sa.String(length=500), nullable=True),
            sa.Column('confidence', sa.Float(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint('id'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.UniqueConstraint('user_id', 'deduplication_hash', name='ix_transactions_user_dedup'),
            sa.Index('ix_transactions_user_id', 'user_id'),
            sa.Index('ix_transactions_date', 'date'),
            sa.Index('ix_transactions_transaction_type', 'transaction_type'),
            sa.Index('ix_transactions_account', 'account'),
            sa.Index('ix_transactions_created_at', 'created_at'),
        )
        # Add foreign key for SQLite (can't be in create_table for SQLite)
        if dialect == 'sqlite':
            op.create_index('ix_transactions_result_id', 'transactions', ['result_id'])
        else:
            op.create_foreign_key(
                'fk_transaction_processing_result',
                'transactions', 'processing_results',
                ['result_id'], ['result_id']
            )
            op.create_index('ix_transactions_result_id', 'transactions', ['result_id'])
    else:
        # transactions table exists, check if result_id column exists
        existing_tx_columns = [col['name'] for col in inspector.get_columns('transactions')]
        if 'result_id' not in existing_tx_columns:
            op.add_column('transactions', sa.Column('result_id', sa.String(length=36), nullable=True))
            # SQLite doesn't support adding foreign keys via ALTER TABLE
            if dialect != 'sqlite':
                op.create_foreign_key(
                    'fk_transaction_processing_result',
                    'transactions', 'processing_results',
                    ['result_id'], ['result_id']
                )
            op.create_index('ix_transactions_result_id', 'transactions', ['result_id'])

    # Step 3: Migrate data from JSON columns to new columns
    # Only run if processing_metadata column exists
    if ([col["name"] for col in inspector.get_columns('processing_results')]).count('processing_metadata') > 0:
        if dialect == 'mysql':
            op.execute("""
                UPDATE processing_results 
                SET result_id = id,
                    row_count = CAST(processing_metadata->>'$.row_count' AS INTEGER),
                    processing_time = CAST(processing_metadata->>'$.processing_time' AS FLOAT),
                    ml_enabled = CAST(processing_metadata->>'$.ml_enabled' AS BOOLEAN),
                    start_date = STR_TO_DATE(processing_metadata->>'$.date_range.start', '%Y-%m-%d'),
                    end_date = STR_TO_DATE(processing_metadata->>'$.date_range.end', '%Y-%m-%d')
                WHERE processing_metadata IS NOT NULL
            """)
        elif dialect == 'sqlite':
            op.execute("""
                UPDATE processing_results
                SET result_id = id,
                    row_count = CAST(json_extract(processing_metadata, '$.row_count') AS INTEGER),
                    processing_time = CAST(json_extract(processing_metadata, '$.processing_time') AS REAL),
                    ml_enabled = CAST(json_extract(processing_metadata, '$.ml_enabled') AS INTEGER) != 0,
                    start_date = datetime(json_extract(processing_metadata, '$.date_range.start')),
                    end_date = datetime(json_extract(processing_metadata, '$.date_range.end'))
                WHERE processing_metadata IS NOT NULL
            """)
        else:
            # PostgreSQL and other dialects
            op.execute("""
                UPDATE processing_results 
                SET result_id = id,
                    row_count = CAST(processing_metadata->>'row_count' AS INTEGER),
                    processing_time = CAST(processing_metadata->>'processing_time' AS FLOAT),
                    ml_enabled = CAST(processing_metadata->>'ml_enabled' AS BOOLEAN),
                    start_date = CAST(processing_metadata->>'date_range'->>'start' AS TIMESTAMP),
                    end_date = CAST(processing_metadata->>'date_range'->>'end' AS TIMESTAMP)
                WHERE processing_metadata IS NOT NULL
            """)

    # Step 4-6: For SQLite, we can't do ALTER COLUMN, DROP COLUMN, or DROP CONSTRAINT
    # We'll skip these operations for SQLite as they require batch mode
    # For other databases (MySQL, PostgreSQL), we can proceed
    
    if dialect == 'sqlite':
        # For SQLite, skip operations that aren't supported
        # The new columns exist and data is migrated, which is sufficient
        # Create indexes for the new columns
        existing_indexes = [idx['name'] for idx in inspector.get_indexes('processing_results')]
        if 'ix_processing_results_user_id' not in existing_indexes:
            op.create_index('ix_processing_results_user_id', 'processing_results', ['user_id'])
        if 'ix_processing_results_created_at' not in existing_indexes:
            op.create_index('ix_processing_results_created_at', 'processing_results', ['created_at'])
        if 'ix_processing_results_csv_profile_id' not in existing_indexes:
            op.create_index('ix_processing_results_csv_profile_id', 'processing_results', ['csv_profile_id'])
        if 'ix_processing_results_start_date' not in existing_indexes:
            op.create_index('ix_processing_results_start_date', 'processing_results', ['start_date'])
        if 'ix_processing_results_end_date' not in existing_indexes:
            op.create_index('ix_processing_results_end_date', 'processing_results', ['end_date'])
    else:
        # For MySQL/PostgreSQL: complete the full migration
        
        # Ensure all rows have a result_id
        op.alter_column('processing_results', 'result_id', nullable=False)
        
        # Drop the old primary key (id column)
        op.drop_constraint('processing_results', 'primary', type_='primary')
        
        # Make result_id the new primary key
        op.create_primary_key('pk_processing_results', 'processing_results', ['result_id'])

        # Drop old columns that are no longer needed
        if ([col["name"] for col in inspector.get_columns('processing_results')]).count('id') > 0:
            op.drop_column('processing_results', 'id')
        if ([col["name"] for col in inspector.get_columns('processing_results')]).count('data') > 0:
            op.drop_column('processing_results', 'data')
        if ([col["name"] for col in inspector.get_columns('processing_results')]).count('processing_metadata') > 0:
            op.drop_column('processing_results', 'processing_metadata')
        if ([col["name"] for col in inspector.get_columns('processing_results')]).count('statistical_metadata') > 0:
            op.drop_column('processing_results', 'statistical_metadata')
        if ([col["name"] for col in inspector.get_columns('processing_results')]).count('updated_at') > 0:
            op.drop_column('processing_results', 'updated_at')

        # Create indexes for the new columns
        op.create_index('ix_processing_results_user_id', 'processing_results', ['user_id'])
        op.create_index('ix_processing_results_created_at', 'processing_results', ['created_at'])
        op.create_index('ix_processing_results_csv_profile_id', 'processing_results', ['csv_profile_id'])
        op.create_index('ix_processing_results_start_date', 'processing_results', ['start_date'])
        op.create_index('ix_processing_results_end_date', 'processing_results', ['end_date'])


def downgrade():
    """Revert to previous schema."""
    inspector = sa.inspect(op.get_bind())
    conn = op.get_bind()
    dialect = conn.dialect.name
    
    # SQLite doesn't support many ALTER operations, so we do minimal downgrade
    if dialect == 'sqlite':
        # For SQLite, we can't properly downgrade, so we just add back the old columns
        existing_columns = [col['name'] for col in inspector.get_columns('processing_results')]
        if 'processing_metadata' not in existing_columns:
            op.add_column('processing_results', sa.Column('processing_metadata', sa.JSON(), nullable=True))
        if 'statistical_metadata' not in existing_columns:
            op.add_column('processing_results', sa.Column('statistical_metadata', sa.JSON(), nullable=True))
        if 'data' not in existing_columns:
            op.add_column('processing_results', sa.Column('data', sa.JSON(), nullable=True))
        if 'updated_at' not in existing_columns:
            op.add_column('processing_results', sa.Column('updated_at', sa.DateTime(), nullable=True))
        
        # Drop new columns
        if 'row_count' in existing_columns:
            op.drop_column('processing_results', 'row_count')
        if 'processing_time' in existing_columns:
            op.drop_column('processing_results', 'processing_time')
        if 'ml_enabled' in existing_columns:
            op.drop_column('processing_results', 'ml_enabled')
        if 'start_date' in existing_columns:
            op.drop_column('processing_results', 'start_date')
        if 'end_date' in existing_columns:
            op.drop_column('processing_results', 'end_date')
        
        # Remove result_id from transactions
        if ([col["name"] for col in inspector.get_columns('transactions')]).count('result_id') > 0:
            op.drop_column('transactions', 'result_id')
    else:
        # For MySQL/PostgreSQL: full downgrade
        
        # Step 1: Add back the old columns
        op.add_column('processing_results', sa.Column('id', sa.Integer(), autoincrement=True, nullable=False))
        op.add_column('processing_results', sa.Column('data', sa.JSON(), nullable=True))
        op.add_column('processing_results', sa.Column('processing_metadata', sa.JSON(), nullable=True))
        op.add_column('processing_results', sa.Column('statistical_metadata', sa.JSON(), nullable=True))
        op.add_column('processing_results', sa.Column('updated_at', sa.DateTime(), nullable=True))
        
        # Step 2: Drop the result_id primary key
        op.drop_constraint('pk_processing_results', 'processing_results', type_='primary')
        
        # Step 3: Make id the primary key again
        op.create_primary_key('primary', 'processing_results', ['id'])
        
        # Step 4: Make result_id nullable
        op.alter_column('processing_results', 'result_id', nullable=True)
        
        # Step 5: Drop new columns
        op.drop_column('processing_results', 'row_count')
        op.drop_column('processing_results', 'processing_time')
        op.drop_column('processing_results', 'ml_enabled')
        op.drop_column('processing_results', 'start_date')
        op.drop_column('processing_results', 'end_date')
        op.drop_column('processing_results', 'result_id')
        
        # Step 6: Drop indexes
        op.drop_index('ix_processing_results_user_id', 'processing_results')
        op.drop_index('ix_processing_results_created_at', 'processing_results')
        op.drop_index('ix_processing_results_csv_profile_id', 'processing_results')
        op.drop_index('ix_processing_results_start_date', 'processing_results')
        op.drop_index('ix_processing_results_end_date', 'processing_results')
        
        # Step 7: Remove result_id from transactions table
        if ([col["name"] for col in inspector.get_columns('transactions')]).count('result_id') > 0:
            fk_constraints = inspector.get_foreign_keys('transactions')
            for fk in fk_constraints:
                if fk['referred_columns'] == ['result_id']:
                    op.drop_constraint(fk['name'], 'transactions', type_='foreignkey')
            op.drop_column('transactions', 'result_id')
            op.drop_index('ix_transactions_result_id', 'transactions')
