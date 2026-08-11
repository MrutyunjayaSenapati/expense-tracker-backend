from datetime import date, datetime, timezone
from typing import List, Optional, Tuple
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.achievement import Achievement, UserAchievement
from app.db.models.streak import UserStreak


class GamificationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_streak(self, user_id: uuid.UUID) -> UserStreak:
        result = await self.db.execute(
            select(UserStreak).where(UserStreak.user_id == user_id)
        )
        streak = result.scalars().first()
        if not streak:
            streak = UserStreak(
                user_id=user_id,
                current_streak=0,
                longest_streak=0,
                last_activity_date=None,
            )
            self.db.add(streak)
            await self.db.flush()
            await self.db.refresh(streak)
        return streak

    async def update_streak(
        self,
        streak: UserStreak,
        current_streak: int,
        longest_streak: int,
        last_activity_date: date,
    ) -> UserStreak:
        streak.current_streak = current_streak
        streak.longest_streak = max(longest_streak, streak.longest_streak)
        streak.last_activity_date = last_activity_date
        await self.db.flush()
        await self.db.refresh(streak)
        return streak

    async def get_all_achievements(self) -> List[Achievement]:
        result = await self.db.execute(select(Achievement).order_by(Achievement.name.asc()))
        return list(result.scalars().all())

    async def get_user_achievements(
        self, user_id: uuid.UUID
    ) -> List[Tuple[Achievement, datetime]]:
        result = await self.db.execute(
            select(Achievement, UserAchievement.unlocked_at)
            .join(UserAchievement, UserAchievement.achievement_id == Achievement.id)
            .where(UserAchievement.user_id == user_id)
        )
        return [(row[0], row[1]) for row in result.all()]

    async def get_achievement_by_code(self, code: str) -> Optional[Achievement]:
        result = await self.db.execute(select(Achievement).where(Achievement.code == code))
        return result.scalars().first()

    async def is_achievement_unlocked(self, user_id: uuid.UUID, achievement_id: uuid.UUID) -> bool:
        result = await self.db.execute(
            select(UserAchievement).where(
                UserAchievement.user_id == user_id,
                UserAchievement.achievement_id == achievement_id,
            )
        )
        return result.scalars().first() is not None

    async def unlock_achievement(
        self, user_id: uuid.UUID, achievement_id: uuid.UUID
    ) -> UserAchievement:
        user_ach = UserAchievement(
            user_id=user_id,
            achievement_id=achievement_id,
            unlocked_at=datetime.now(timezone.utc),
        )
        self.db.add(user_ach)
        await self.db.flush()
        return user_ach

    async def seed_system_achievements(self, achievements_data: List[dict]) -> None:
        for item in achievements_data:
            existing = await self.get_achievement_by_code(item["code"])
            if not existing:
                ach = Achievement(
                    code=item["code"],
                    name=item["name"],
                    description=item["description"],
                    icon=item.get("icon"),
                )
                self.db.add(ach)
        await self.db.flush()
