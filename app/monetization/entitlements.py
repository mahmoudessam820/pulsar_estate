from app.monetization.limits import PLAN_LIMITS
from app.monetization.plans import Plan
from app.monetization.usage import UsageService
from app.auth.models import User


class EntitlementService:
    def __init__(self, usage_service: UsageService):
        self.usage_service = usage_service

    async def check_pipeline_access(self, user: User) -> bool:
        plan = Plan(user.plan)
        limit = PLAN_LIMITS[plan]["daily_runs"]

        return await self.usage_service.can_run(user.id, limit)

    async def record_pipeline_run(self, user: User) -> None:
        await self.usage_service.record_run(user.id)
