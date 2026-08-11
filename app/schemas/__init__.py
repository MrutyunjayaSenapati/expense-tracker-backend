from app.schemas.common import ErrorDetail, ErrorResponse, ListResponse, PaginatedResponse, PaginationMetadata
from app.schemas.auth import (
    LogoutRequest,
    RefreshTokenRequest,
    RefreshTokenResponse,
    RegisterResponse,
    TokenResponse,
    UserLogin,
    UserRegister,
    UserResponse,
)
from app.schemas.account import AccountCreate, AccountListResponse, AccountResponse, AccountUpdate
from app.schemas.category import CategoryCreate, CategoryListResponse, CategoryResponse, CategoryUpdate
from app.schemas.transaction import (
    AccountSummary,
    CategorySummary,
    TransactionCreate,
    TransactionListResponse,
    TransactionResponse,
    TransactionUpdate,
)
from app.schemas.budget import (
    BudgetCategoryCreate,
    BudgetCategoryResponse,
    BudgetCreate,
    BudgetListResponse,
    BudgetResponse,
    BudgetUpdate,
)
from app.schemas.recurring import (
    RecurringTransactionCreate,
    RecurringTransactionListResponse,
    RecurringTransactionResponse,
    RecurringTransactionUpdate,
)
from app.schemas.dashboard import (
    CategorySpendingItem,
    DashboardBudgetSummary,
    DashboardResponse,
    StreakSummary,
)
from app.schemas.report import (
    PeriodInfo,
    ReportAccountItem,
    ReportCategoryItem,
    ReportResponse,
    ReportTrendItem,
)
from app.schemas.notification import NotificationListResponse, NotificationResponse
from app.schemas.gamification import AchievementResponse, GamificationResponse

__all__ = [
    "ErrorDetail",
    "ErrorResponse",
    "ListResponse",
    "PaginatedResponse",
    "PaginationMetadata",
    "UserRegister",
    "UserLogin",
    "UserResponse",
    "RegisterResponse",
    "TokenResponse",
    "RefreshTokenRequest",
    "RefreshTokenResponse",
    "LogoutRequest",
    "AccountCreate",
    "AccountUpdate",
    "AccountResponse",
    "AccountListResponse",
    "CategoryCreate",
    "CategoryUpdate",
    "CategoryResponse",
    "CategoryListResponse",
    "TransactionCreate",
    "TransactionUpdate",
    "TransactionResponse",
    "TransactionListResponse",
    "AccountSummary",
    "CategorySummary",
    "BudgetCreate",
    "BudgetUpdate",
    "BudgetResponse",
    "BudgetListResponse",
    "BudgetCategoryCreate",
    "BudgetCategoryResponse",
    "RecurringTransactionCreate",
    "RecurringTransactionUpdate",
    "RecurringTransactionResponse",
    "RecurringTransactionListResponse",
    "DashboardResponse",
    "DashboardBudgetSummary",
    "CategorySpendingItem",
    "StreakSummary",
    "ReportResponse",
    "PeriodInfo",
    "ReportCategoryItem",
    "ReportAccountItem",
    "ReportTrendItem",
    "NotificationResponse",
    "NotificationListResponse",
    "AchievementResponse",
    "GamificationResponse",
]
