"""Add original-value columns to transactions, drop corrected_notice from corrections.

Corrections become merchant rules carrying partner and category only
(notices are per-transaction exceptions), and transactions capture their
original category and notice values before the first user correction so
original-vs-corrected display and undo are possible.

Revision ID: 006
Revises: 005
Create Date: 2026-10-01 00:00:00.000000

"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '006'
down_revision: Union[str, None] = '005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    """Add original columns to transactions; drop corrected_notice."""
    op.add_column(
        'transactions',
        sa.Column('original_category_id', sa.String(length=50), nullable=True)
    )
    op.add_column(
        'transactions',
        sa.Column('original_notice', sa.String(length=500), nullable=True)
    )
    op.drop_column('corrections', 'corrected_notice')


def downgrade():
    """Restore corrected_notice; drop original columns."""
    op.add_column(
        'corrections',
        sa.Column('corrected_notice', sa.String(length=500), nullable=True)
    )
    op.drop_column('transactions', 'original_notice')
    op.drop_column('transactions', 'original_category_id')
