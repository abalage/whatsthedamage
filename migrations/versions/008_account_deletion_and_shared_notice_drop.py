"""Account deletion scheduling and shared correction notice removal.

Adds users.scheduled_deletion_at for the account deletion flow (7-day
grace period, see the retention policy) and drops the unused
shared_corrections.corrected_notice column: notices are never shared
(merchant names and categories only, epic Decision #8).

Revision ID: 008
Revises: 007
Create Date: 2026-10-06 00:00:00.000000

"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '008'
down_revision: Union[str, None] = '007'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    """Add deletion scheduling and drop the shared notice column."""
    op.add_column(
        'users',
        sa.Column('scheduled_deletion_at', sa.DateTime(), nullable=True)
    )
    op.drop_column('shared_corrections', 'corrected_notice')


def downgrade():
    """Restore the shared notice column and drop deletion scheduling."""
    op.add_column(
        'shared_corrections',
        sa.Column('corrected_notice', sa.String(length=500), nullable=True)
    )
    op.drop_column('users', 'scheduled_deletion_at')
