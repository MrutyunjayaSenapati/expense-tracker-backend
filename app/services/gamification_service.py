from datetime import date, datetime, timedelta, timezone
from typing import List, Tuple
import uuid
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.notification import Notification
from app.db.models.streak import UserStreak
from app.db.models.transaction import Transaction
from app.repositories.gamification_repository import GamificationRepository
from app.schemas.gamification import AchievementResponse, GamificationResponse
from app.schemas.dashboard import StreakSummary


class GamificationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = GamificationRepository(db)

    async def get_summary(self, user_id: uuid.UUID) -> GamificationResponse:
        streak = await self.repo.get_or_create_streak(user_id)
        all_achievements = await self.repo.get_all_achievements()
        unlocked_items = await self.repo.get_user_achievements(user_id)

        unlocked_dict = {ach.id: dt for ach, dt in unlocked_items}

        achievement_responses: List[AchievementResponse] = []
        for ach in all_achievements:
            is_unlocked = ach.id in unlocked_dict
            achievement_responses.append(
                AchievementResponse(
                    code=ach.code,
                    name=ach.name,
                    description=ach.description,
                    icon=ach.icon,
                    unlocked=is_unlocked,
                    unlocked_at=unlocked_dict.get(ach.id),
                )
            )

        return GamificationResponse(
            streak=StreakSummary(
                current=streak.current_streak,
                longest=streak.longest_streak,
            ),
            achievements=achievement_responses,
        )

    async def record_transaction_activity(
        self, user_id: uuid.UUID, activity_date: date
    ) -> None:
        streak = await self.repo.get_or_create_streak(user_id)
        last_date = streak.last_activity_date

        if last_date is None:
            streak.current_streak = 1
            streak.longest_streak = max(1, streak.longest_streak)
            streak.last_activity_date = activity_date
        elif last_date == activity_date:
            pass  # Same day, keep streak
        elif last_date == activity_date - timedelta(days=1):
            streak.current_streak += 1
            streak.longest_streak = max(streak.current_streak, streak.longest_streak)
            streak.last_activity_date = activity_date
        elif activity_date > last_date:
            streak.current_streak = 1
            streak.last_activity_date = activity_date

        await self.db.flush()

        # Check Achievements
        await self._check_achievements(user_id, streak)

    async def _check_achievements(self, user_id: uuid.UUID, streak: UserStreak) -> None:
        # First transaction
        first_ach = await self.repo.get_achievement_by_code("FIRST_TRANSACTION")
        if first_ach and not await self.repo.is_achievement_unlocked(user_id, first_ach.id):
            await self._unlock(user_id, first_ach.id, first_ach.name)

        # 7-day streak
        if streak.current_streak >= 7:
            seven_ach = await self.repo.get_achievement_by_code("SEVEN_DAY_STREAK")
            if seven_ach and not await self.repo.is_achievement_unlocked(user_id, seven_ach.id):
                await self._unlock(user_id, seven_ach.id, seven_ach.name)

        # 50 transactions
        total_txns_res = await self.db.execute(
            select(func.count(Transaction.id)).where(Transaction.user_id == user_id)
        )
        total_txns = total_txns_res.scalar_one()
        if total_txns >= 50:
            fifty_ach = await self.repo.get_achievement_by_code("FIFTY_TRANSACTIONS")
            if fifty_ach and not await self.repo.is_achievement_unlocked(user_id, fifty_ach.id):
                await self._unlock(user_id, fifty_ach.id, fifty_ach.name)

    async def _unlock(self, user_id: uuid.UUID, achievement_id: uuid.UUID, achievement_name: str) -> None:
        await self.repo.unlock_achievement(user_id, achievement_id)
        # Create notification
        notif = Notification(
            user_id=user_id,
            type="ACHIEVEMENT_UNLOCKED",
            title="Achievement Unlocked! 🏆",
            message=f"You unlocked '{achievement_name}'!",
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(notif)
        await self.db.flush()
