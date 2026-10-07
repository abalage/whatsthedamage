"""Add shared_corrections table for anonymized correction sharing.

Stores anonymized shared corrections contributed by users who opted in
to sharing (merchant names + categories only, no user linkage).

Revision ID: 007
Revises: 006
Create Date: 2026-10-02 00:00:00.000000

"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '007'
down_revision: Union[str, None] = '006'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    """Create the shared_corrections table."""
    op.create_table(
        'shared_corrections',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('original_partner_hash', sa.String(length=64), nullable=False),
        sa.Column('corrected_partner', sa.String(length=255), nullable=True),
        sa.Column('corrected_category_id', sa.String(length=50), nullable=False),
        sa.Column('corrected_notice', sa.String(length=500), nullable=True),
        sa.Column('contributed_at', sa.DateTime(), nullable=False),
        sa.Column('contribution_count', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        'ix_shared_corrections_original_hash',
        'shared_corrections',
        ['original_partner_hash'],
        unique=True
    )
    op.create_index(
        'ix_shared_corrections_category',
        'shared_corrections',
        ['corrected_category_id'],
        unique=False
    )
    op.create_index(
        'ix_shared_corrections_contributed_at',
        'shared_corrections',
        ['contributed_at'],
        unique=False
    )


def downgrade():
    """Drop the shared_corrections table."""
    op.drop_index(
        'ix_shared_corrections_contributed_at', table_name='shared_corrections'
    )
    op.drop_index(
        'ix_shared_corrections_category', table_name='shared_corrections'
    )
    op.drop_index(
        'ix_shared_corrections_original_hash', table_name='shared_corrections'
    )
    op.drop_table('shared_corrections')
