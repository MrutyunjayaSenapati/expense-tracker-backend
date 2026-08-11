from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.gamification import GamificationResponse
from app.services.gamification_service import GamificationService

router = APIRouter(prefix="/gamification", tags=["Gamification"])


@router.get(
    "",
    response_model=GamificationResponse,
    summary="Get user streak and unlocked achievements",
)
async def get_gamification(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = GamificationService(db)
    return await service.get_summary(current_user.id)
