"""Add corrections table for user-specific transaction corrections.

Stores per-user corrections (partner, category, notice) keyed by the
original partner name, applied to newly uploaded transactions.

Revision ID: 005
Revises: 004
Create Date: 2026-10-01 00:00:00.000000

"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '005'
down_revision: Union[str, None] = '004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    """Create the corrections table."""
    op.create_table(
        'corrections',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('original_partner', sa.String(length=255), nullable=False),
        sa.Column('corrected_partner', sa.String(length=255), nullable=True),
        sa.Column('corrected_category_id', sa.String(length=50), nullable=True),
        sa.Column('corrected_notice', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        'ix_corrections_user_id', 'corrections', ['user_id'], unique=False
    )
    op.create_index(
        'ix_corrections_original_partner', 'corrections', ['original_partner'],
        unique=False
    )


def downgrade():
    """Drop the corrections table."""
    op.drop_index('ix_corrections_original_partner', table_name='corrections')
    op.drop_index('ix_corrections_user_id', table_name='corrections')
    op.drop_table('corrections')
