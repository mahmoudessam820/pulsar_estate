from pydantic import BaseModel, Field, ConfigDict

from datetime import datetime
from typing import Literal, Optional


# Request Schemas


class RunPipelineRequest(BaseModel):
    """Trigger a data pipeline run"""

    query: str = Field(
        ...,
        min_length=3,
        max_length=200,
        description="Search query for pipeline execution",
        examples=["Dubai real estate market trends", "London property prices 2026"],
    )


class UpgradeRoleRequest(BaseModel):
    """Request to upgrade a user's role"""

    user_id: str = Field(..., description="Target user ID to upgrade")
    role: Literal["user", "developer", "admin"] = Field(
        ..., description="New role to assign to the user"
    )


class DowngradeRoleRequest(BaseModel):
    """Request to downgrade a user to regular user"""

    user_id: str = Field(..., description="Target user ID to downgrade")
    role: Literal["user"] = Field(
        ...,
        description="Role to assign to the user (only 'user' allowed for downgrade)",
    )


class UpgradePlanRequest(BaseModel):
    """Request to upgrade a user's subscription plan"""

    user_id: str = Field(..., description="Target user ID to upgrade")
    plan: Literal["free", "pro", "enterprise"] = Field(
        ..., description="New subscription plan"
    )


class DowngradePlanRequest(BaseModel):
    """Request to downgrade a user to free plan"""

    user_id: str = Field(..., description="Target user ID to downgrade")


# Response Schemas


class PipelineRunResponse(BaseModel):
    """Response after pipeline execution"""

    message: str
    query: str
    status: Literal["success", "failed"]
    executed_at: datetime = Field(default_factory=datetime.now)


class RoleUpdateResponse(BaseModel):
    """Response after role upgrade"""

    message: str
    user_id: str
    email: str
    old_role: str
    new_role: str
    updated_at: datetime = Field(default_factory=datetime.now)


class PlanUpdateResponse(BaseModel):
    """Response after plan change"""

    message: str
    user_id: str
    email: str
    old_plan: str
    new_plan: str
    updated_at: datetime = Field(default_factory=datetime.now)


class DowngradePlanResponse(BaseModel):
    """Response after manual downgrade"""

    message: str
    user_id: str
    email: str
    old_plan: str
    new_plan: str
    subscription_status: str = "manual_downgrade"
    updated_at: datetime = Field(default_factory=datetime.now)


class DowngradeRoleResponse(BaseModel):
    """Response after role downgrade"""

    message: str
    user_id: str
    email: str
    old_role: str
    new_role: str = "user"
    updated_at: datetime = Field(default_factory=datetime.now)


# Error Response Schema


class AdminErrorResponse(BaseModel):
    """Standardized error response for admin endpoints"""

    model_config = ConfigDict(json_schema_extra={"example": {"detail": "Unauthorized"}})

    detail: str
    status_code: Optional[int] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
