import uuid
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel
from app.schemas.transaction import TransactionResponse


class DashboardBudgetSummary(BaseModel):
    id: Optional[uuid.UUID] = None
    name: str = "Monthly Budget"
    amount: Decimal = Decimal("0.00")
    spent: Decimal = Decimal("0.00")
    remaining: Decimal = Decimal("0.00")
    percentage_used: float = 0.0
    status: str = "HEALTHY"


class CategorySpendingItem(BaseModel):
    category_id: uuid.UUID
    category_name: str
    category_icon: Optional[str] = None
    category_color: Optional[str] = None
    amount: Decimal
    percentage: float
    transaction_count: int = 0


class StreakSummary(BaseModel):
    current: int = 0
    longest: int = 0


class DashboardResponse(BaseModel):
    balance: Decimal
    income: Decimal
    expenses: Decimal
    savings: Decimal
    savings_percentage: float
    budget: Optional[DashboardBudgetSummary] = None
    top_categories: List[CategorySpendingItem] = []
    recent_transactions: List[TransactionResponse] = []
    streak: StreakSummary = StreakSummary()
