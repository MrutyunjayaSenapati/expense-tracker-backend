from fastapi import APIRouter
from app.api.v1.accounts import router as accounts_router
from app.api.v1.auth import router as auth_router
from app.api.v1.budgets import router as budgets_router
from app.api.v1.categories import router as categories_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.gamification import router as gamification_router
from app.api.v1.groups import router as groups_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.recurring_transactions import router as recurring_router
from app.api.v1.reports import router as reports_router
from app.api.v1.splits import router as splits_router
from app.api.v1.transactions import router as transactions_router

api_v1_router = APIRouter()

api_v1_router.include_router(auth_router)
api_v1_router.include_router(accounts_router)
api_v1_router.include_router(categories_router)
api_v1_router.include_router(transactions_router)
api_v1_router.include_router(budgets_router)
api_v1_router.include_router(recurring_router)
api_v1_router.include_router(splits_router)
api_v1_router.include_router(groups_router)
api_v1_router.include_router(dashboard_router)
api_v1_router.include_router(reports_router)
api_v1_router.include_router(notifications_router)
api_v1_router.include_router(gamification_router)
