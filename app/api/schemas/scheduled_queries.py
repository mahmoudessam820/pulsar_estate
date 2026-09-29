import uuid
from datetime import datetime, time
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


# Request
class ScheduledQueryCreateRequest(BaseModel):
    query_text: str = Field(
        ..., min_length=3, max_length=500, description="The market query to run daily"
    )
    execution_time: str = Field(
        ..., description="Time in 12-hour format, e.g., '08:20 PM' or '8:20 AM'"
    )
    timezone: str = Field(
        default="UTC",
        max_length=50,
        description="Timezone for the execution time (e.g., 'UTC', 'United Arab Emirates/Dubai')",
    )


# Response
class ScheduledQueryResponse(BaseModel):
    id: uuid.UUID
    query_text: str
    execution_time: time
    timezone: str
    is_active: bool
    last_run_at: Optional[datetime] = None
    next_run_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ScheduledQueryToggleRequest(BaseModel):
    is_active: bool = Field(..., description="True to activate, False to pause")
