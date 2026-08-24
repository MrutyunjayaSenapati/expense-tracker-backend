"""create user push tokens table

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-08-24 14:50:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from app.db.base import GUID

# revision identifiers, used by Alembic.
revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, None] = 'c3d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'user_push_tokens',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('user_id', GUID(), nullable=False),
        sa.Column('push_token', sa.String(length=255), nullable=False),
        sa.Column('device_type', sa.String(length=20), server_default='android', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_push_tokens_user_id'), 'user_push_tokens', ['user_id'], unique=False)
    op.create_index(op.f('ix_user_push_tokens_push_token'), 'user_push_tokens', ['push_token'], unique=True)
    op.create_index(op.f('ix_user_push_tokens_is_active'), 'user_push_tokens', ['is_active'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_user_push_tokens_is_active'), table_name='user_push_tokens')
    op.drop_index(op.f('ix_user_push_tokens_push_token'), table_name='user_push_tokens')
    op.drop_index(op.f('ix_user_push_tokens_user_id'), table_name='user_push_tokens')
    op.drop_table('user_push_tokens')
