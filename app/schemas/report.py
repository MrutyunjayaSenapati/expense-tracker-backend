import uuid
from datetime import date
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel


class PeriodInfo(BaseModel):
    type: str = "week"
    start_date: date
    end_date: date


class ReportCategoryItem(BaseModel):
    category_id: uuid.UUID
    category_name: str
    category_icon: Optional[str] = None
    category_color: Optional[str] = None
    amount: Decimal
    percentage: float
    transaction_count: int = 0


class ReportAccountItem(BaseModel):
    account_id: uuid.UUID
    account_name: str
    account_type: str
    amount: Decimal
    percentage: float
    transaction_count: int = 0


class ReportTrendItem(BaseModel):
    date: str
    income: Decimal = Decimal("0.00")
    expense: Decimal = Decimal("0.00")


class ReportResponse(BaseModel):
    period: PeriodInfo
    income: Decimal
    expenses: Decimal
    savings: Decimal
    savings_percentage: float = 0.0
    categories: List[ReportCategoryItem] = []
    accounts: List[ReportAccountItem] = []
    trend: List[ReportTrendItem] = []
