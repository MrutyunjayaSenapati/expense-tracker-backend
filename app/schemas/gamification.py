from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from app.schemas.dashboard import StreakSummary


class AchievementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    name: str
    description: str
    icon: Optional[str] = None
    unlocked: bool = False
    unlocked_at: Optional[datetime] = None


class GamificationResponse(BaseModel):
    streak: StreakSummary
    achievements: List[AchievementResponse]
