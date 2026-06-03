import logging
from datetime import datetime, timezone

from app.payments.stripe import FakeStripeGateway
from app.data.repositories.base import UserRepositoryBase


class SubscriptionService:
    def __init__(self, user_repo: UserRepositoryBase):
        self.user_repo = user_repo
        self.gateway = FakeStripeGateway()

    async def subscribe_user(self, user_id: str, plan: str):
        subscription = await self.gateway.create_subscription(user_id, plan)

        await self.user_repo.update_subscription(
            user_id=user_id,
            subscription_data={
                "plan": plan,
                "subscription_id": subscription["subscription_id"],
                "subscription_status": "active",
                "current_period_end": subscription["current_period_end"],
                "updated_at": datetime.now(timezone.utc).isoformat(),
            },
        )

        return subscription

    async def cancel_subscription(self, user_id: str, subscription_id: str):
        await self.gateway.cancel_subscription(subscription_id)

        await self.user_repo.update_subscription(
            user_id=user_id,
            subscription_data={
                "plan": "free",
                "subscription_status": "canceled",
                "updated_at": datetime.now(timezone.utc).isoformat(),
            },
        )

    async def downgrade_expired_users(self):
        users = await self.user_repo.list_users()
        now = datetime.now(timezone.utc)

        for user in users:
            period_end = user.get("current_period_end")

            if not period_end:
                continue

            if datetime.fromisoformat(period_end) < now:
                await self.user_repo.update_subscription(
                    user_id=user["id"],
                    subscription_data={
                        "plan": "free",
                        "subscription_status": "expired",
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    },
                )

                logging.info(
                    f"Downgraded user {user['id']} due to expired subscription"
                )
