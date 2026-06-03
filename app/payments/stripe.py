import uuid
from datetime import datetime, timedelta, timezone

from app.payments.base import PaymentGatewayBase


class FakeStripeGateway(PaymentGatewayBase):
    async def create_subscription(self, user_id: str, plan: str) -> dict:
        subscription_id = str(uuid.uuid4())

        return {
            "subscription_id": subscription_id,
            "user_id": user_id,
            "plan": plan,
            "status": "active",
            "checkout_url": (f"https://fake-stripe.com/checkout/{subscription_id}"),
            "current_period_end": (
                datetime.now(timezone.utc) + timedelta(days=30)
            ).isoformat(),
        }

    async def cancel_subscription(self, subscription_id: str) -> dict:
        return {"subscription_id": subscription_id, "status": "canceled"}
