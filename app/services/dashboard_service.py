from datetime import date, datetime, time, timezone
from decimal import Decimal
from typing import List
import uuid
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.account import Account
from app.repositories.account_repository import AccountRepository
from app.repositories.budget_repository import BudgetRepository
from app.repositories.gamification_repository import GamificationRepository
from app.repositories.transaction_repository import TransactionRepository
from app.schemas.dashboard import (
    CategorySpendingItem,
    DashboardBudgetSummary,
    DashboardResponse,
    StreakSummary,
)
from app.schemas.transaction import TransactionResponse
from app.services.budget_service import BudgetService


class DashboardService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.account_repo = AccountRepository(db)
        self.txn_repo = TransactionRepository(db)
        self.budget_repo = BudgetRepository(db)
        self.budget_service = BudgetService(db)
        self.gamification_repo = GamificationRepository(db)

    async def get_dashboard(self, user_id: uuid.UUID) -> DashboardResponse:
        today = date.today()
        # Month bounds
        first_day_month = date(today.year, today.month, 1)
        if today.month == 12:
            last_day_month = date(today.year + 1, 1, 1)
        else:
            last_day_month = date(today.year, today.month + 1, 1)

        start_dt = datetime.combine(first_day_month, time.min, tzinfo=timezone.utc)
        end_dt = datetime.combine(last_day_month, time.min, tzinfo=timezone.utc)

        # 1. Total balance across active accounts
        balance_res = await self.db.execute(
            select(func.coalesce(func.sum(Account.balance), Decimal("0.00")))
            .where(Account.user_id == user_id, Account.is_active.is_(True))
        )
        total_balance = balance_res.scalar_one()

        # 2. Monthly income & expense
        income, expenses = await self.txn_repo.get_totals_by_user_and_period(
            user_id=user_id, start_date=start_dt, end_date=end_dt
        )

        savings = income - expenses
        savings_pct = float(round((savings / income) * 100, 2)) if income > 0 else 0.0

        # 3. Active budget summary
        active_budget = await self.budget_repo.get_active_budget_for_date(user_id, today)
        budget_summary = None
        if active_budget:
            enriched_budget = await self.budget_service._enrich_budget(active_budget)
            budget_summary = DashboardBudgetSummary(
                id=enriched_budget.id,
                name=enriched_budget.name,
                amount=enriched_budget.amount,
                spent=enriched_budget.spent,
                remaining=enriched_budget.remaining,
                percentage_used=enriched_budget.percentage_used,
                status=enriched_budget.status,
            )

        # 4. Top categories spending this month
        category_rows = await self.txn_repo.get_category_spending_by_user(
            user_id=user_id, start_date=start_dt, end_date=end_dt, limit=5
        )
        top_categories: List[CategorySpendingItem] = []
        for cat, amt, count in category_rows:
            pct = float(round((amt / expenses) * 100, 2)) if expenses > 0 else 0.0
            top_categories.append(
                CategorySpendingItem(
                    category_id=cat.id,
                    category_name=cat.name,
                    category_icon=cat.icon,
                    category_color=cat.color,
                    amount=amt,
                    percentage=pct,
                    transaction_count=count,
                )
            )

        # 5. Recent transactions (top 5)
        recent_txns_models = await self.txn_repo.get_recent_by_user(user_id=user_id, limit=5)
        recent_txns = [TransactionResponse.model_validate(t) for t in recent_txns_models]

        # 6. Streak summary
        streak = await self.gamification_repo.get_or_create_streak(user_id)
        streak_summary = StreakSummary(
            current=streak.current_streak,
            longest=streak.longest_streak,
        )

        return DashboardResponse(
            balance=total_balance,
            income=income,
            expenses=expenses,
            savings=savings,
            savings_percentage=savings_pct,
            budget=budget_summary,
            top_categories=top_categories,
            recent_transactions=recent_txns,
            streak=streak_summary,
        )
