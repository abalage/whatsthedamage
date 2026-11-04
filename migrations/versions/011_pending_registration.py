"""Add pending registration columns to the users table.

Two-phase registration: a row with registration_confirmed_at NULL is a
pending registration. It becomes a real account only when the user
confirms possession of the one-time recovery code via
POST /api/v2/auth/register/confirm. Pending rows expire after
pending_expires_at and are physically deleted by the retention purge
job, so abandoned registrations never become committed accounts.

Revision ID: 011
Revises: 010
Create Date: 2026-11-10 00:00:00.000000

"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '011'
down_revision: Union[str, None] = '010'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    """Add the pending-registration columns to the users table."""
    with op.batch_alter_table('users') as batch_op:
        batch_op.add_column(
            sa.Column('registration_confirmed_at', sa.DateTime(), nullable=True)
        )
        batch_op.add_column(
            sa.Column('pending_token_hash', sa.Text(), nullable=True)
        )
        batch_op.add_column(
            sa.Column('pending_expires_at', sa.DateTime(), nullable=True)
        )
        batch_op.create_index(
            'ix_users_pending_token_hash', ['pending_token_hash'], unique=True
        )


def downgrade():
    """Drop the pending-registration columns from the users table."""
    with op.batch_alter_table('users') as batch_op:
        batch_op.drop_index('ix_users_pending_token_hash')
        batch_op.drop_column('pending_expires_at')
        batch_op.drop_column('pending_token_hash')
        batch_op.drop_column('registration_confirmed_at')
