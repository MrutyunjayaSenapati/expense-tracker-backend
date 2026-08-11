from datetime import datetime, time, timezone
from decimal import Decimal
from typing import List, Optional
import uuid
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import ResourceNotFoundError, ValidationAppError
from app.db.models.budget import Budget, BudgetCategory
from app.db.models.category import Category
from app.db.models.transaction import Transaction
from app.repositories.budget_repository import BudgetRepository
from app.repositories.category_repository import CategoryRepository
from app.schemas.budget import (
    BudgetCategoryCreate,
    BudgetCategoryResponse,
    BudgetCreate,
    BudgetResponse,
    BudgetUpdate,
)


class BudgetService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.budget_repo = BudgetRepository(db)
        self.category_repo = CategoryRepository(db)

    async def list_budgets(self, user_id: uuid.UUID) -> List[BudgetResponse]:
        budgets = await self.budget_repo.get_all_by_user(user_id=user_id, active_only=True)
        return [await self._enrich_budget(budget) for budget in budgets]

    async def get_budget(self, user_id: uuid.UUID, budget_id: uuid.UUID) -> BudgetResponse:
        budget = await self.budget_repo.get_by_user_and_id(user_id=user_id, budget_id=budget_id)
        if not budget or not budget.is_active:
            raise ResourceNotFoundError("Budget not found", "BUDGET_NOT_FOUND")
        return await self._enrich_budget(budget)

    async def create_budget(self, user_id: uuid.UUID, payload: BudgetCreate) -> BudgetResponse:
        if payload.end_date < payload.start_date:
            raise ValidationAppError(
                "End date must be after start date",
                code="INVALID_DATE_RANGE",
            )

        budget = Budget(
            user_id=user_id,
            name=payload.name.strip(),
            amount=payload.amount,
            period=payload.period,
            start_date=payload.start_date,
            end_date=payload.end_date,
            is_active=True,
        )
        self.db.add(budget)
        await self.db.flush()

        if payload.categories:
            for cat_payload in payload.categories:
                # Verify category ownership
                cat = await self.category_repo.get_by_user_and_id(user_id, cat_payload.category_id)
                if not cat or not cat.is_active:
                    raise ValidationAppError(
                        f"Category {cat_payload.category_id} not found or inactive",
                        code="INVALID_CATEGORY",
                    )
                b_cat = BudgetCategory(
                    budget_id=budget.id,
                    category_id=cat_payload.category_id,
                    amount=cat_payload.amount,
                )
                self.db.add(b_cat)

        await self.db.commit()
        return await self.get_budget(user_id, budget.id)

    async def update_budget(
        self, user_id: uuid.UUID, budget_id: uuid.UUID, payload: BudgetUpdate
    ) -> BudgetResponse:
        budget = await self.budget_repo.get_by_user_and_id(user_id=user_id, budget_id=budget_id)
        if not budget or not budget.is_active:
            raise ResourceNotFoundError("Budget not found", "BUDGET_NOT_FOUND")

        if payload.name is not None:
            budget.name = payload.name.strip()
        if payload.amount is not None:
            budget.amount = payload.amount
        if payload.start_date is not None:
            budget.start_date = payload.start_date
        if payload.end_date is not None:
            budget.end_date = payload.end_date

        if budget.end_date < budget.start_date:
            raise ValidationAppError("End date must be after start date", "INVALID_DATE_RANGE")

        if payload.categories is not None:
            # Replace categories
            for old_cat in budget.categories:
                await self.db.delete(old_cat)
            await self.db.flush()

            for cat_payload in payload.categories:
                cat = await self.category_repo.get_by_user_and_id(user_id, cat_payload.category_id)
                if not cat or not cat.is_active:
                    raise ValidationAppError("Category not found or inactive", "INVALID_CATEGORY")
                b_cat = BudgetCategory(
                    budget_id=budget.id,
                    category_id=cat_payload.category_id,
                    amount=cat_payload.amount,
                )
                self.db.add(b_cat)

        await self.db.commit()
        return await self.get_budget(user_id, budget.id)

    async def delete_budget(self, user_id: uuid.UUID, budget_id: uuid.UUID) -> None:
        budget = await self.budget_repo.get_by_user_and_id(user_id=user_id, budget_id=budget_id)
        if not budget or not budget.is_active:
            raise ResourceNotFoundError("Budget not found", "BUDGET_NOT_FOUND")

        budget.is_active = False
        await self.db.commit()

    async def _enrich_budget(self, budget: Budget) -> BudgetResponse:
        start_dt = datetime.combine(budget.start_date, time.min, tzinfo=timezone.utc)
        end_dt = datetime.combine(budget.end_date, time.max, tzinfo=timezone.utc)

        # 1. Total spent across all expense transactions in period
        total_spent_res = await self.db.execute(
            select(func.coalesce(func.sum(Transaction.amount), Decimal("0.00")))
            .where(
                Transaction.user_id == budget.user_id,
                Transaction.type == "EXPENSE",
                Transaction.transaction_date >= start_dt,
                Transaction.transaction_date <= end_dt,
            )
        )
        spent = total_spent_res.scalar_one()

        remaining = max(Decimal("0.00"), budget.amount - spent)
        pct_used = float(round((spent / budget.amount) * 100, 2)) if budget.amount > 0 else 0.0

        status_str = "HEALTHY"
        if pct_used > 100:
            status_str = "OVER_BUDGET"
        elif pct_used >= 90:
            status_str = "NEAR_LIMIT"
        elif pct_used >= 80:
            status_str = "WARNING"

        # 2. Enrich category allocations
        category_responses: List[BudgetCategoryResponse] = []
        for b_cat in budget.categories:
            cat_spent_res = await self.db.execute(
                select(func.coalesce(func.sum(Transaction.amount), Decimal("0.00")))
                .where(
                    Transaction.user_id == budget.user_id,
                    Transaction.category_id == b_cat.category_id,
                    Transaction.type == "EXPENSE",
                    Transaction.transaction_date >= start_dt,
                    Transaction.transaction_date <= end_dt,
                )
            )
            cat_spent = cat_spent_res.scalar_one()
            cat_remaining = max(Decimal("0.00"), b_cat.amount - cat_spent)
            cat_pct = float(round((cat_spent / b_cat.amount) * 100, 2)) if b_cat.amount > 0 else 0.0

            category_responses.append(
                BudgetCategoryResponse(
                    id=b_cat.id,
                    category_id=b_cat.category_id,
                    category_name=b_cat.category.name if b_cat.category else None,
                    category_icon=b_cat.category.icon if b_cat.category else None,
                    amount=b_cat.amount,
                    spent=cat_spent,
                    remaining=cat_remaining,
                    percentage_used=cat_pct,
                )
            )

        return BudgetResponse(
            id=budget.id,
            name=budget.name,
            amount=budget.amount,
            period=budget.period,
            start_date=budget.start_date,
            end_date=budget.end_date,
            spent=spent,
            remaining=remaining,
            percentage_used=pct_used,
            status=status_str,
            categories=category_responses,
        )
