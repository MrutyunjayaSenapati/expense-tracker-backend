import uuid
from datetime import date
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class BudgetCategoryCreate(BaseModel):
    category_id: uuid.UUID
    amount: Decimal = Field(..., gt=Decimal("0.00"), max_digits=14, decimal_places=2)


class BudgetCategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    category_id: uuid.UUID
    category_name: Optional[str] = None
    category_icon: Optional[str] = None
    amount: Decimal
    spent: Decimal = Decimal("0.00")
    remaining: Decimal = Decimal("0.00")
    percentage_used: float = 0.0


class BudgetCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    amount: Decimal = Field(..., gt=Decimal("0.00"), max_digits=14, decimal_places=2)
    period: str = Field(default="MONTHLY", pattern="^(MONTHLY|WEEKLY|YEARLY|CUSTOM)$")
    start_date: date
    end_date: date
    categories: Optional[List[BudgetCategoryCreate]] = Field(default_factory=list)


class BudgetUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    amount: Optional[Decimal] = Field(None, gt=Decimal("0.00"), max_digits=14, decimal_places=2)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    categories: Optional[List[BudgetCategoryCreate]] = None


class BudgetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    amount: Decimal
    period: str
    start_date: date
    end_date: date
    spent: Decimal = Decimal("0.00")
    remaining: Decimal = Decimal("0.00")
    percentage_used: float = 0.0
    status: str = "HEALTHY"  # HEALTHY, WARNING, NEAR_LIMIT, OVER_BUDGET
    categories: List[BudgetCategoryResponse] = Field(default_factory=list)


class BudgetListResponse(BaseModel):
    items: List[BudgetResponse]
