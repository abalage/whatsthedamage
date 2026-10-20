"""Drop the sessions.token_hash_prefix column.

The token hash prefix was a lookup optimization whose prefix-based
lookup path has been removed; sessions are validated by their full
token hash. Drops the column and its index.

Revision ID: 010
Revises: 009
Create Date: 2026-10-13 00:00:00.000000

"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '010'
down_revision: Union[str, None] = '009'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    """Drop the token hash prefix column and its index."""
    op.drop_index('ix_sessions_token_hash_prefix', table_name='sessions')
    with op.batch_alter_table('sessions') as batch_op:
        batch_op.drop_column('token_hash_prefix')


def downgrade():
    """Restore the token hash prefix column and its index."""
    with op.batch_alter_table('sessions') as batch_op:
        batch_op.add_column(
            sa.Column('token_hash_prefix', sa.String(length=8),
                      nullable=False, server_default='')
        )
    op.create_index(
        'ix_sessions_token_hash_prefix', 'sessions', ['token_hash_prefix']
    )
