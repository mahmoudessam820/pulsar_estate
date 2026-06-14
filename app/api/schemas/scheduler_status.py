from typing import Optional
from datetime import datetime

from pydantic import BaseModel, Field


class SchedulerStatusResponse(BaseModel):
    """Response schema for /scheduler/status endpoint"""

    model_config = {
        "json_schema_extra": {
            "example": {
                "last_run": "2026-06-11T10:30:00Z",
                "last_duration_seconds": 135.5,
                "last_error": None,
            }
        }
    }

    last_run: Optional[datetime] = Field(
        default=None,
        description="Timestamp of the last scheduler run (null if never run)",
    )

    last_duration_seconds: Optional[float] = Field(
        default=None,
        ge=0,
        description="Duration of the last run in seconds (null if never run or failed immediately)",
    )

    last_error: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Error message from the last run (null if successful or never run)",
    )
