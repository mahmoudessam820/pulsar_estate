from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, ConfigDict


# Request Schemas
class SubscribeRequest(BaseModel):
    """Payload for subscribing to a billing plan"""

    plan: Literal["pro", "enterprise"] = Field(
        ...,
        description="The billing plan to subscribe to",
        examples=["pro", "enterprise"],
    )


# Response Schemas
class SubscriptionPublic(BaseModel):
    """Sanitized subscription details returned to clients"""

    model_config = ConfigDict(
        from_attributes=True
    )  # Enables ORM ↔ Pydantic conversion | But not implemented yet.

    subscription_id: str
    plan: str
    status: str
    current_period_end: datetime
    # 🔧 Add/remove fields to match your actual Subscription DB model
    # e.g., trial_ends_at: datetime | None, next_billing_date: datetime, etc.


class SubscribeResponse(BaseModel):
    message: str
    subscription: SubscriptionPublic


class CancelResponse(BaseModel):
    message: str
