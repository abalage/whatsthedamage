"""GDPR consent demonstrability and shared correction withdrawal.

Adds users.opted_in_at / users.opted_out_at (consent demonstrability,
GDPR Art. 7(1)) and users.revoke_shared_corrections (a default-off
option recorded with the account deletion request). Creates the
shared_correction_contributions link table so a user's contributions
to the anonymized shared corrections can be withdrawn when the
account is deleted (GDPR Art. 7(3), Art. 17).

Revision ID: 009
Revises: 008
Create Date: 2026-10-07 00:00:00.000000

"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '009'
down_revision: Union[str, None] = '008'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    """Add consent columns and the contribution link table."""
    op.add_column('users', sa.Column('opted_in_at', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('opted_out_at', sa.DateTime(), nullable=True))
    op.add_column(
        'users',
        sa.Column(
            'revoke_shared_corrections',
            sa.Boolean(),
            nullable=False,
            server_default=sa.false()
        )
    )
    op.create_table(
        'shared_correction_contributions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('shared_correction_id', sa.Integer(), nullable=False),
        sa.Column('contribution_count', sa.Integer(), nullable=False),
        sa.Column('contributed_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ['user_id'], ['users.id'],
            name=op.f('fk_shared_correction_contributions_user_id_users')
        ),
        sa.ForeignKeyConstraint(
            ['shared_correction_id'], ['shared_corrections.id'],
            name=op.f(
                'fk_shared_correction_contributions_shared_correction_id'
                '_shared_corrections'
            )
        ),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_shared_correction_contributions')),
        sa.UniqueConstraint(
            'user_id', 'shared_correction_id',
            name='uq_contribution_user_shared_correction'
        ),
    )
    op.create_index(
        op.f('ix_shared_correction_contributions_user_id'),
        'shared_correction_contributions',
        ['user_id'],
        unique=False,
    )


def downgrade():
    """Drop the contribution link table and consent columns."""
    op.drop_index(
        op.f('ix_shared_correction_contributions_user_id'),
        table_name='shared_correction_contributions',
    )
    op.drop_table('shared_correction_contributions')
    op.drop_column('users', 'revoke_shared_corrections')
    op.drop_column('users', 'opted_out_at')
    op.drop_column('users', 'opted_in_at')
