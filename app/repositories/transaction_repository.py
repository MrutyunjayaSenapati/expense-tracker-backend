from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
import uuid
from sqlalchemy import desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.db.models.account import Account
from app.db.models.category import Category
from app.db.models.transaction import Transaction
from app.repositories.base import BaseRepository


class TransactionRepository(BaseRepository[Transaction]):
    def __init__(self, db: AsyncSession):
        super().__init__(Transaction, db)

    async def get_by_user_and_id(self, user_id: uuid.UUID, transaction_id: uuid.UUID) -> Optional[Transaction]:
        result = await self.db.execute(
            select(Transaction)
            .options(selectinload(Transaction.account), selectinload(Transaction.category))
            .where(
                Transaction.id == transaction_id,
                Transaction.user_id == user_id,
            )
        )
        return result.scalars().first()

    async def list_filtered(
        self,
        user_id: uuid.UUID,
        page: int = 1,
        limit: int = 20,
        category_id: Optional[uuid.UUID] = None,
        account_id: Optional[uuid.UUID] = None,
        txn_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        min_amount: Optional[Decimal] = None,
        max_amount: Optional[Decimal] = None,
        search: Optional[str] = None,
        sort: str = "transaction_date",
        order: str = "desc",
    ) -> Tuple[List[Transaction], int]:
        limit = min(max(1, limit), 100)
        offset = (max(1, page) - 1) * limit

        query = (
            select(Transaction)
            .join(Transaction.category)
            .options(selectinload(Transaction.account), selectinload(Transaction.category))
            .where(Transaction.user_id == user_id)
        )

        if category_id:
            query = query.where(Transaction.category_id == category_id)
        if account_id:
            query = query.where(Transaction.account_id == account_id)
        if txn_type:
            query = query.where(Transaction.type == txn_type.upper())
        if start_date:
            query = query.where(Transaction.transaction_date >= start_date)
        if end_date:
            query = query.where(Transaction.transaction_date <= end_date)
        if min_amount is not None:
            query = query.where(Transaction.amount >= min_amount)
        if max_amount is not None:
            query = query.where(Transaction.amount <= max_amount)
        if search:
            search_pattern = f"%{search.strip()}%"
            query = query.where(
                or_(
                    Transaction.merchant.ilike(search_pattern),
                    Transaction.note.ilike(search_pattern),
                    Category.name.ilike(search_pattern),
                )
            )

        # Count total items
        count_subquery = query.with_only_columns(func.count(Transaction.id)).order_by(None)
        total_result = await self.db.execute(count_subquery)
        total = total_result.scalar_one()

        # Sorting
        sort_column = Transaction.transaction_date
        if sort == "amount":
            sort_column = Transaction.amount
        elif sort == "created_at":
            sort_column = Transaction.created_at

        if order.lower() == "asc":
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())

        query = query.offset(offset).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def get_recent_by_user(self, user_id: uuid.UUID, limit: int = 10) -> List[Transaction]:
        query = (
            select(Transaction)
            .options(selectinload(Transaction.account), selectinload(Transaction.category))
            .where(Transaction.user_id == user_id)
            .order_by(Transaction.transaction_date.desc())
            .limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_totals_by_user_and_period(
        self,
        user_id: uuid.UUID,
        start_date: datetime,
        end_date: datetime,
    ) -> Tuple[Decimal, Decimal]:
        """Returns (total_income, total_expense) in date range."""
        query = (
            select(
                Transaction.type,
                func.coalesce(func.sum(Transaction.amount), Decimal("0.00")),
            )
            .where(
                Transaction.user_id == user_id,
                Transaction.transaction_date >= start_date,
                Transaction.transaction_date <= end_date,
            )
            .group_by(Transaction.type)
        )
        result = await self.db.execute(query)
        rows = result.all()

        income = Decimal("0.00")
        expense = Decimal("0.00")
        for txn_type, total in rows:
            if txn_type == "INCOME":
                income = total
            elif txn_type == "EXPENSE":
                expense = total
        return income, expense

    async def get_category_spending_by_user(
        self,
        user_id: uuid.UUID,
        start_date: datetime,
        end_date: datetime,
        limit: Optional[int] = None,
    ) -> List[Tuple[Category, Decimal, int]]:
        """Returns list of (Category, total_spent, txn_count) for expenses in date range."""
        query = (
            select(
                Category,
                func.coalesce(func.sum(Transaction.amount), Decimal("0.00")).label("total_spent"),
                func.count(Transaction.id).label("txn_count"),
            )
            .join(Transaction, Transaction.category_id == Category.id)
            .where(
                Transaction.user_id == user_id,
                Transaction.type == "EXPENSE",
                Transaction.transaction_date >= start_date,
                Transaction.transaction_date <= end_date,
            )
            .group_by(Category.id)
            .order_by(desc("total_spent"))
        )
        if limit:
            query = query.limit(limit)

        result = await self.db.execute(query)
        return [(row[0], row[1], row[2]) for row in result.all()]

    async def get_account_spending_by_user(
        self,
        user_id: uuid.UUID,
        start_date: datetime,
        end_date: datetime,
    ) -> List[Tuple[Account, Decimal, int]]:
        query = (
            select(
                Account,
                func.coalesce(func.sum(Transaction.amount), Decimal("0.00")).label("total_spent"),
                func.count(Transaction.id).label("txn_count"),
            )
            .join(Transaction, Transaction.account_id == Account.id)
            .where(
                Transaction.user_id == user_id,
                Transaction.type == "EXPENSE",
                Transaction.transaction_date >= start_date,
                Transaction.transaction_date <= end_date,
            )
            .group_by(Account.id)
            .order_by(desc("total_spent"))
        )
        result = await self.db.execute(query)
        return [(row[0], row[1], row[2]) for row in result.all()]
