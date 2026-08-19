import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, GUID, TimestampMixin

if TYPE_CHECKING:
    from app.db.models.user import User


class SplitBill(Base, TimestampMixin):
    __tablename__ = "split_bills"

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
    paid_by_user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    your_share: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    is_settled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    creator: Mapped["User"] = relationship("User", foreign_keys=[creator_id])
    paid_by: Mapped["User"] = relationship("User", foreign_keys=[paid_by_user_id])
    participants: Mapped[List["SplitParticipant"]] = relationship(
        "SplitParticipant",
        back_populates="split_bill",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_split_bills_creator_date", "creator_id", "date"),
        Index("ix_split_bills_paid_by", "paid_by_user_id"),
    )


class SplitParticipant(Base, TimestampMixin):
    __tablename__ = "split_participants"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    split_bill_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("split_bills.id", ondelete="CASCADE"),
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
    phone_or_upi: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    amount_owed: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    is_paid: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    split_bill: Mapped["SplitBill"] = relationship("SplitBill", back_populates="participants")
    user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[user_id])

    __table_args__ = (
        Index("ix_split_participants_user", "user_id"),
        Index("ix_split_participants_bill", "split_bill_id"),
    )
