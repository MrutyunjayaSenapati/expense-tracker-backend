"""create group expenses tables

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-08-19 16:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from app.db.base import GUID

# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. groups
    op.create_table(
        'groups',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('creator_id', GUID(), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('category', sa.String(length=50), server_default='HOME', nullable=False),
        sa.Column('invite_code', sa.String(length=12), nullable=False),
        sa.Column('currency', sa.String(length=10), server_default='INR', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['creator_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_groups_creator_id', 'groups', ['creator_id'], unique=False)
    op.create_index('ix_groups_invite_code', 'groups', ['invite_code'], unique=True)

    # 2. group_members
    op.create_table(
        'group_members',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('group_id', GUID(), nullable=False),
        sa.Column('user_id', GUID(), nullable=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('email_or_phone', sa.String(length=100), nullable=True),
        sa.Column('role', sa.String(length=20), server_default='MEMBER', nullable=False),
        sa.Column('joined_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['group_id'], ['groups.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_group_members_group_id', 'group_members', ['group_id'], unique=False)
    op.create_index('ix_group_members_user_id', 'group_members', ['user_id'], unique=False)
    op.create_index('ix_group_members_group_user', 'group_members', ['group_id', 'user_id'], unique=False)

    # 3. group_expenses
    op.create_table(
        'group_expenses',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('group_id', GUID(), nullable=False),
        sa.Column('paid_by_user_id', GUID(), nullable=True),
        sa.Column('payer_name', sa.String(length=100), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('amount', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('date', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['group_id'], ['groups.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['paid_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_group_expenses_group_id', 'group_expenses', ['group_id'], unique=False)
    op.create_index('ix_group_expenses_paid_by_user_id', 'group_expenses', ['paid_by_user_id'], unique=False)
    op.create_index('ix_group_expenses_group_date', 'group_expenses', ['group_id', 'date'], unique=False)

    # 4. group_expense_splits
    op.create_table(
        'group_expense_splits',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('expense_id', GUID(), nullable=False),
        sa.Column('member_id', GUID(), nullable=False),
        sa.Column('amount_owed', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['expense_id'], ['group_expenses.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['member_id'], ['group_members.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_group_expense_splits_expense_id', 'group_expense_splits', ['expense_id'], unique=False)
    op.create_index('ix_group_expense_splits_member_id', 'group_expense_splits', ['member_id'], unique=False)

    # 5. group_settlements
    op.create_table(
        'group_settlements',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('group_id', GUID(), nullable=False),
        sa.Column('from_user_id', GUID(), nullable=False),
        sa.Column('to_user_id', GUID(), nullable=False),
        sa.Column('amount', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('settled_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['group_id'], ['groups.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['from_user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['to_user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_group_settlements_group_id', 'group_settlements', ['group_id'], unique=False)
    op.create_index('ix_group_settlements_from_user_id', 'group_settlements', ['from_user_id'], unique=False)
    op.create_index('ix_group_settlements_to_user_id', 'group_settlements', ['to_user_id'], unique=False)


def downgrade() -> None:
    op.drop_table('group_settlements')
    op.drop_table('group_expense_splits')
    op.drop_table('group_expenses')
    op.drop_table('group_members')
    op.drop_table('groups')
