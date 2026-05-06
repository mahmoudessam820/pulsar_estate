from app.data.repositories.base import UsageRepositoryBase


class UsageService:
    def __init__(self, usage_repo: UsageRepositoryBase):
        self.usage_repo = usage_repo

    async def can_run(self, user_id: str, limit: int) -> bool:
        used = await self.usage_repo.count_today(user_id)
        return used < limit

    async def record_run(self, user_id: str) -> None:
        await self.usage_repo.increment(user_id)
