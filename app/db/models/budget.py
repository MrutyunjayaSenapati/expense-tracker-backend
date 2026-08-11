import uuid
from datetime import date
from decimal import Decimal
from typing import List, TYPE_CHECKING
from sqlalchemy import Boolean, Date, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, GUID, TimestampMixin

if TYPE_CHECKING:
    from app.db.models.user import User
    from app.db.models.category import Category


class Budget(Base, TimestampMixin):
    __tablename__ = "budgets"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    period: Mapped[str] = mapped_column(String(50), default="MONTHLY", nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="budgets")
    categories: Mapped[List["BudgetCategory"]] = relationship(
        "BudgetCategory",
        back_populates="budget",
        cascade="all, delete-orphan",
    )


class BudgetCategory(Base):
    __tablename__ = "budget_categories"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    budget_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("budgets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    category_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)

    # Relationships
    budget: Mapped["Budget"] = relationship("Budget", back_populates="categories")
    category: Mapped["Category"] = relationship("Category", back_populates="budget_allocations")
