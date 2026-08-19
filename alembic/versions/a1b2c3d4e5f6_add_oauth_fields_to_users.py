"""add_oauth_fields_to_users

Revision ID: a1b2c3d4e5f6
Revises: 77f7c5cf272b
Create Date: 2026-08-18 12:45:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '77f7c5cf272b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Handle nullable password_hash and new OAuth fields
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column('password_hash', existing_type=sa.Text(), nullable=True)
        batch_op.add_column(sa.Column('avatar_url', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('auth_provider', sa.String(length=20), server_default='email', nullable=False))
        batch_op.add_column(sa.Column('google_id', sa.String(length=255), nullable=True))
        batch_op.create_index('ix_users_google_id', ['google_id'], unique=False)


def downgrade() -> None:
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_index('ix_users_google_id')
        batch_op.drop_column('google_id')
        batch_op.drop_column('auth_provider')
        batch_op.drop_column('avatar_url')
        batch_op.alter_column('password_hash', existing_type=sa.Text(), nullable=False)
