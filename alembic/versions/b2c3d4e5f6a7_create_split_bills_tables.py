"""create_split_bills_tables

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-08-19 16:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from app.db.base import GUID


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create split_bills table
    op.create_table(
        'split_bills',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('creator_id', GUID(), nullable=False),
        sa.Column('paid_by_user_id', GUID(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('total_amount', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('your_share', sa.Numeric(precision=14, scale=2), server_default='0.00', nullable=False),
        sa.Column('date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_settled', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['creator_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['paid_by_user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_split_bills_creator_date', 'split_bills', ['creator_id', 'date'], unique=False)
    op.create_index('ix_split_bills_paid_by', 'split_bills', ['paid_by_user_id'], unique=False)
    op.create_index('ix_split_bills_is_settled', 'split_bills', ['is_settled'], unique=False)

    # 2. Create split_participants table
    op.create_table(
        'split_participants',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('split_bill_id', GUID(), nullable=False),
        sa.Column('user_id', GUID(), nullable=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('phone_or_upi', sa.String(length=100), nullable=True),
        sa.Column('amount_owed', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('is_paid', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('paid_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['split_bill_id'], ['split_bills.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_split_participants_user', 'split_participants', ['user_id'], unique=False)
    op.create_index('ix_split_participants_bill', 'split_participants', ['split_bill_id'], unique=False)
    op.create_index('ix_split_participants_is_paid', 'split_participants', ['is_paid'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_split_participants_is_paid', table_name='split_participants')
    op.drop_index('ix_split_participants_bill', table_name='split_participants')
    op.drop_index('ix_split_participants_user', table_name='split_participants')
    op.drop_table('split_participants')

    op.drop_index('ix_split_bills_is_settled', table_name='split_bills')
    op.drop_index('ix_split_bills_paid_by', table_name='split_bills')
    op.drop_index('ix_split_bills_creator_date', table_name='split_bills')
    op.drop_table('split_bills')
