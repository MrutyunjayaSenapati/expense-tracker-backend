from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.report import ReportResponse
from app.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get(
    "",
    response_model=ReportResponse,
    summary="Get spending report aggregations",
)
async def get_report(
    period: str = Query("week", pattern="^week$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ReportService(db)
    return await service.get_weekly_report(current_user.id)
