"""Change transaction date column from String(20) to DateTime.

This migration converts the date column in the transactions table from String(20)
storing Unix epoch timestamps to DateTime type for native date operations.

The migration:
1. Converts existing string epoch values to DateTime
2. Changes the column type from String(20) to DateTime
3. Maintains data integrity by preserving all existing date values

Revision ID: 004
Revises: 003
Create Date: 2026-09-23 00:00:00.000000

"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    """Upgrade database schema: convert date column from String to DateTime."""
    inspector = sa.inspect(op.get_bind())
    conn = op.get_bind()
    dialect = conn.dialect.name

    # Only proceed if transactions table exists
    if not inspector.has_table('transactions'):
        return

    # Check if date column exists and is String type
    existing_columns = {col['name']: col for col in inspector.get_columns('transactions')}
    if 'date' not in existing_columns:
        return

    date_column = existing_columns['date']
    
    # Check if already DateTime (migration already applied)
    if isinstance(date_column['type'], sa.DateTime):
        return

    # For SQLite, we need to use a different approach
    if dialect == 'sqlite':
        # SQLite doesn't support ALTER COLUMN TYPE easily
        # We need to:
        # 1. Create a new temporary table
        # 2. Copy data with converted date
        # 3. Drop old table
        # 4. Rename new table

        # Step 1: Create new table with DateTime column
        op.create_table(
            'transactions_new',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('result_id', sa.String(length=36), nullable=True),
            sa.Column('date', sa.DateTime(), nullable=False),
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
            sa.Index('ix_transactions_user_id_new', 'user_id'),
            sa.Index('ix_transactions_date_new', 'date'),
            sa.Index('ix_transactions_transaction_type_new', 'transaction_type'),
            sa.Index('ix_transactions_account_new', 'account'),
            sa.Index('ix_transactions_created_at_new', 'created_at'),
        )
        # Add result_id foreign key and index (SQLite needs separate step)
        op.create_index('ix_transactions_result_id_new', 'transactions_new', ['result_id'])

        # Step 2: Copy data with date conversion (epoch string to DateTime)
        op.execute("""
            INSERT INTO transactions_new (
                id, user_id, result_id, date, transaction_type, original_partner,
                amount, currency, account, deduplication_hash, category_id,
                partner, notice, confidence, created_at, updated_at
            )
            SELECT
                id, user_id, result_id,
                datetime(date, 'unixepoch') as date,  -- Convert epoch string to DateTime
                transaction_type, original_partner,
                amount, currency, account, deduplication_hash, category_id,
                partner, notice, confidence, created_at, updated_at
            FROM transactions
        """)

        # Step 3: Drop old table
        op.drop_table('transactions')

        # Step 4: Rename new table
        op.rename_table('transactions_new', 'transactions')

        # Recreate indexes with original names
        op.create_index('ix_transactions_user_dedup', 'transactions', ['user_id', 'deduplication_hash'], unique=True)
        op.drop_index('ix_transactions_date_new', 'transactions')
        op.drop_index('ix_transactions_transaction_type_new', 'transactions')
        op.drop_index('ix_transactions_account_new', 'transactions')
        op.drop_index('ix_transactions_created_at_new', 'transactions')
        op.drop_index('ix_transactions_user_id_new', 'transactions')
        op.drop_index('ix_transactions_result_id_new', 'transactions')

    else:
        # For PostgreSQL, MySQL, and other databases
        # First, convert existing data from epoch string to timestamp
        op.execute("""
            UPDATE transactions 
            SET date = CASE 
                WHEN date ~ '^[0-9]+$' THEN to_timestamp(date::bigint)
                ELSE date
            END
            WHERE date ~ '^[0-9]+$'
        """)

        # Then alter the column type
        op.alter_column('transactions', 'date', type_=sa.DateTime(), nullable=False)


def downgrade():
    """Revert: convert date column back from DateTime to String(20)."""
    inspector = sa.inspect(op.get_bind())
    conn = op.get_bind()
    dialect = conn.dialect.name

    # Only proceed if transactions table exists
    if not inspector.has_table('transactions'):
        return

    # Check if date column exists and is DateTime type
    existing_columns = {col['name']: col for col in inspector.get_columns('transactions')}
    if 'date' not in existing_columns:
        return

    date_column = existing_columns['date']
    
    # Check if already String (migration already reverted)
    if isinstance(date_column['type'], sa.String):
        return

    # For SQLite
    if dialect == 'sqlite':
        # Create new table with String column
        op.create_table(
            'transactions_new',
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
            sa.Index('ix_transactions_user_id_new', 'user_id'),
            sa.Index('ix_transactions_date_new', 'date'),
            sa.Index('ix_transactions_transaction_type_new', 'transaction_type'),
            sa.Index('ix_transactions_account_new', 'account'),
            sa.Index('ix_transactions_created_at_new', 'created_at'),
        )
        op.create_index('ix_transactions_result_id_new', 'transactions_new', ['result_id'])

        # Copy data with date conversion (DateTime to epoch string)
        op.execute("""
            INSERT INTO transactions_new (
                id, user_id, result_id, date, transaction_type, original_partner,
                amount, currency, account, deduplication_hash, category_id,
                partner, notice, confidence, created_at, updated_at
            )
            SELECT
                id, user_id, result_id,
                strftime('%s', date) as date,  -- Convert DateTime to epoch string
                transaction_type, original_partner,
                amount, currency, account, deduplication_hash, category_id,
                partner, notice, confidence, created_at, updated_at
            FROM transactions
        """)

        # Drop old table
        op.drop_table('transactions')

        # Rename new table
        op.rename_table('transactions_new', 'transactions')

        # Recreate indexes with original names
        op.create_index('ix_transactions_user_dedup', 'transactions', ['user_id', 'deduplication_hash'], unique=True)
        op.drop_index('ix_transactions_date_new', 'transactions')
        op.drop_index('ix_transactions_transaction_type_new', 'transactions')
        op.drop_index('ix_transactions_account_new', 'transactions')
        op.drop_index('ix_transactions_created_at_new', 'transactions')
        op.drop_index('ix_transactions_user_id_new', 'transactions')
        op.drop_index('ix_transactions_result_id_new', 'transactions')

    else:
        # For PostgreSQL, MySQL, and other databases
        # Convert DateTime back to epoch string
        op.execute("""
            UPDATE transactions 
            SET date = extract(epoch from date)::text
        """)

        # Alter the column type back to String
        op.alter_column('transactions', 'date', type_=sa.String(length=20), nullable=False)
