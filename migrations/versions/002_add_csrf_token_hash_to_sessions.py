"""Add csrf_token_hash to sessions table.

This migration adds the csrf_token_hash column to the sessions table
for CSRF protection support.

Revision ID: 002
Revises: 001
Create Date: 2026-09-18 00:00:00.000000

"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    """Add csrf_token_hash column to sessions table."""
    op.add_column(
        'sessions',
        sa.Column('csrf_token_hash', sa.String(length=64), nullable=True)
    )


def downgrade():
    """Remove csrf_token_hash column from sessions table."""
    op.drop_column('sessions', 'csrf_token_hash')
