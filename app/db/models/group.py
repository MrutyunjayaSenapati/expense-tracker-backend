import uuid
import string
import random
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, GUID, TimestampMixin

if TYPE_CHECKING:
    from app.db.models.user import User


def generate_invite_code(length: int = 6) -> str:
    """Generate a clean 6-character alphanumeric uppercase invite code."""
    chars = string.ascii_uppercase + "23456789"  # exclude confusing 0, 1, I, O
    return "".join(random.choices(chars, k=length))


class Group(Base, TimestampMixin):
    __tablename__ = "groups"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    creator_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    category: Mapped[str] = mapped_column(String(50), default="HOME", nullable=False)  # HOME, TRIP, COUPLE, OTHER
    invite_code: Mapped[str] = mapped_column(
        String(12),
        unique=True,
        nullable=False,
        index=True,
        default=generate_invite_code,
    )
    currency: Mapped[str] = mapped_column(String(10), default="INR", nullable=False)

    # Relationships
    creator: Mapped["User"] = relationship("User", foreign_keys=[creator_id])
    members: Mapped[List["GroupMember"]] = relationship(
        "GroupMember",
        back_populates="group",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    expenses: Mapped[List["GroupExpense"]] = relationship(
        "GroupExpense",
        back_populates="group",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    settlements: Mapped[List["GroupSettlement"]] = relationship(
        "GroupSettlement",
        back_populates="group",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class GroupMember(Base, TimestampMixin):
    __tablename__ = "group_members"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    group_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("groups.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email_or_phone: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    role: Mapped[str] = mapped_column(String(20), default="MEMBER", nullable=False)  # ADMIN, MEMBER
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    group: Mapped["Group"] = relationship("Group", back_populates="members")
    user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[user_id])
    splits: Mapped[List["GroupExpenseSplit"]] = relationship(
        "GroupExpenseSplit",
        back_populates="member",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_group_members_group_user", "group_id", "user_id"),
    )


class GroupExpense(Base, TimestampMixin):
    __tablename__ = "group_expenses"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    group_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("groups.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    paid_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    payer_name: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    group: Mapped["Group"] = relationship("Group", back_populates="expenses")
    paid_by_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[paid_by_user_id])
    splits: Mapped[List["GroupExpenseSplit"]] = relationship(
        "GroupExpenseSplit",
        back_populates="expense",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_group_expenses_group_date", "group_id", "date"),
    )


class GroupExpenseSplit(Base, TimestampMixin):
    __tablename__ = "group_expense_splits"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    expense_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("group_expenses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    member_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("group_members.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    amount_owed: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)

    # Relationships
    expense: Mapped["GroupExpense"] = relationship("GroupExpense", back_populates="splits")
    member: Mapped["GroupMember"] = relationship("GroupMember", back_populates="splits")


class GroupSettlement(Base, TimestampMixin):
    __tablename__ = "group_settlements"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    group_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("groups.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    from_user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    to_user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    settled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    group: Mapped["Group"] = relationship("Group", back_populates="settlements")
    from_user: Mapped["User"] = relationship("User", foreign_keys=[from_user_id])
    to_user: Mapped["User"] = relationship("User", foreign_keys=[to_user_id])
