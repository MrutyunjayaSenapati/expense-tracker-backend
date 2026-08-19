from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from typing import List
import uuid
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.transaction import Transaction
from app.repositories.transaction_repository import TransactionRepository
from app.schemas.report import (
    PeriodInfo,
    ReportAccountItem,
    ReportCategoryItem,
    ReportResponse,
    ReportTrendItem,
)


class ReportService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.txn_repo = TransactionRepository(db)

    async def get_weekly_report(self, user_id: uuid.UUID) -> ReportResponse:
        today = date.today()
        # 7-day period ending today
        start_date = today - timedelta(days=6)
        end_date = today

        start_dt = datetime.combine(start_date, time.min, tzinfo=timezone.utc)
        end_dt = datetime.combine(end_date, time.max, tzinfo=timezone.utc)

        # 1. Totals
        income, expenses = await self.txn_repo.get_totals_by_user_and_period(
            user_id=user_id, start_date=start_dt, end_date=end_dt
        )
        savings = income - expenses
        savings_pct = float(round((savings / income) * 100, 2)) if income > 0 else 0.0

        # 2. Categories breakdown
        category_rows = await self.txn_repo.get_category_spending_by_user(
            user_id=user_id, start_date=start_dt, end_date=end_dt
        )
        categories: List[ReportCategoryItem] = []
        for cat, amt, count in category_rows:
            pct = float(round((amt / expenses) * 100, 2)) if expenses > 0 else 0.0
            categories.append(
                ReportCategoryItem(
                    category_id=cat.id,
                    category_name=cat.name,
                    category_icon=cat.icon,
                    category_color=cat.color,
                    amount=amt,
                    percentage=pct,
                    transaction_count=count,
                )
            )

        # 3. Accounts breakdown
        account_rows = await self.txn_repo.get_account_spending_by_user(
            user_id=user_id, start_date=start_dt, end_date=end_dt
        )
        accounts: List[ReportAccountItem] = []
        for acc, amt, count in account_rows:
            pct = float(round((amt / expenses) * 100, 2)) if expenses > 0 else 0.0
            accounts.append(
                ReportAccountItem(
                    account_id=acc.id,
                    account_name=acc.name,
                    account_type=acc.type,
                    amount=amt,
                    percentage=pct,
                    transaction_count=count,
                )
            )

        # 4. Daily trend for the 7 days
        trend_map = {start_date + timedelta(days=i): {"income": Decimal("0.00"), "expense": Decimal("0.00")} for i in range(7)}

        daily_txns = await self.db.execute(
            select(
                func.date(Transaction.transaction_date).label("txn_d"),
                Transaction.type,
                func.sum(Transaction.amount),
            )
            .where(
                Transaction.user_id == user_id,
                Transaction.transaction_date >= start_dt,
                Transaction.transaction_date <= end_dt,
            )
            .group_by("txn_d", Transaction.type)
        )

        for txn_d_val, t_type, t_sum in daily_txns.all():
            d_key = txn_d_val if isinstance(txn_d_val, date) else date.fromisoformat(str(txn_d_val))
            if d_key in trend_map:
                if t_type == "INCOME":
                    trend_map[d_key]["income"] = t_sum
                elif t_type == "EXPENSE":
                    trend_map[d_key]["expense"] = t_sum

        trend: List[ReportTrendItem] = [
            ReportTrendItem(
                date=d.isoformat(),
                income=vals["income"],
                expense=vals["expense"],
            )
            for d, vals in sorted(trend_map.items())
        ]

        return ReportResponse(
            period=PeriodInfo(type="week", start_date=start_date, end_date=end_date),
            income=income,
            expenses=expenses,
            savings=savings,
            savings_percentage=savings_pct,
            categories=categories,
            accounts=accounts,
            trend=trend,
        )

    async def export_csv(self, user_id: uuid.UUID) -> str:
        import csv
        import io
        from sqlalchemy.orm import selectinload

        txns_result = await self.db.execute(
            select(Transaction)
            .options(
                selectinload(Transaction.category),
                selectinload(Transaction.account),
            )
            .where(Transaction.user_id == user_id)
            .order_by(Transaction.transaction_date.desc())
        )
        txns = txns_result.scalars().all()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "Transaction ID",
            "Date",
            "Time (UTC)",
            "Type",
            "Category",
            "Account",
            "Amount",
            "Merchant",
            "Note",
        ])

        for t in txns:
            dt = t.transaction_date
            d_str = dt.strftime("%Y-%m-%d") if dt else ""
            t_str = dt.strftime("%H:%M:%S") if dt else ""
            cat_name = t.category.name if t.category else "Uncategorized"
            acc_name = t.account.name if t.account else "Default Account"
            writer.writerow([
                str(t.id),
                d_str,
                t_str,
                t.type,
                cat_name,
                acc_name,
                f"{t.amount:.2f}",
                t.merchant or "",
                t.note or "",
            ])

        return output.getvalue()

