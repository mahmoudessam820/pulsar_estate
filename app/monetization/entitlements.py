from app.monetization.limits import PLAN_LIMITS
from app.monetization.plans import Plan
from app.monetization.usage import UsageService
from app.data.repositories.base import ScheduledQueryRepositoryBase
from app.data.models.users import User


class EntitlementService:
    def __init__(
        self,
        usage_service: UsageService,
        scheduled_query_repo: ScheduledQueryRepositoryBase = None,
    ):
        self.usage_service = usage_service
        self.scheduled_query_repo = scheduled_query_repo

    async def check_pipeline_access(self, user: User) -> bool:
        plan = Plan(user.plan)
        limit = PLAN_LIMITS[plan]["daily_runs"]

        return await self.usage_service.can_run(user.id, limit)

    async def record_pipeline_run(self, user: User) -> None:
        await self.usage_service.record_run(user.id)

    async def check_scheduled_query_access(self, user: User) -> bool:
        if not self.scheduled_query_repo:
            raise ValueError(
                "ScheduledQueryRepository not provided to EntitlementService"
            )

        plan = Plan(user.plan)
        limit = PLAN_LIMITS[plan]["scheduled_queries"]
        current_count = await self.scheduled_query_repo.count_active_by_user(
            str(user.id)
        )

        return current_count < limit
