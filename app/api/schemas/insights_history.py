import re
from typing import Optional
from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict, field_validator


# Date Parser Helper


def parse_custom_date(value) -> datetime:
    """
    Parse date strings like "2026, 6, 3" → datetime
    Handles both string and datetime inputs
    """
    if isinstance(value, datetime):
        return value

    # Match "YYYY, M, D" or "YYYY, MM, DD" format
    match = re.match(r"(\d{4}),\s*(\d{1,2}),\s*(\d{1,2})", str(value))
    if match:
        year, month, day = map(int, match.groups())
        return datetime(year, month, day)

    # Fallback: try ISO format
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        raise ValueError(f"Unable to parse date: {value}")


# Individual History Item


class InsightsHistoryItem(BaseModel):
    """Single insight history record"""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "a9beb6f6-c40b-413c-9c57-9f33b76b23eb",
                "query": "Dubai Luxury Residential Real Estate Market Size And Trends Analysis",
                "summary": "The UAE real estate market is experiencing strong growth...",
                "confidence_score": 74.4,
                "timestamp": "2026, 6, 3",
                "duration_seconds": 131.49,
                "error": None,
            }
        },
    )

    id: str = Field(..., description="Unique history record identifier (UUID)")
    query: str = Field(
        ..., description="Search query that was executed", max_length=500
    )

    summary: str = Field(
        ..., description="Executive summary of the generated insight", max_length=5000
    )

    confidence_score: Optional[float] = Field(
        default=None,
        ge=0,
        le=100,
        description="Confidence score for this insight (0-100). Null if generation failed.",
    )

    timestamp: datetime = Field(..., description="When the insight was generated")

    duration_seconds: float = Field(
        ..., ge=0, description="Total processing time in seconds"
    )

    error: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Error message if generation failed, null if successful",
    )

    # Auto-parse the unusual date format
    @field_validator("timestamp", mode="before")
    @classmethod
    def parse_timestamp(cls, value):
        return parse_custom_date(value)


# Wrapper Response Model


class InsightsHistory(BaseModel):
    """Response wrapper for /insights/history endpoint"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "insights_history_list": [
                    {
                        "id": "a9beb6f6-c40b-413c-9c57-9f33b76b23eb",
                        "query": "Dubai Luxury Residential Real Estate Market Size And Trends Analysis",
                        "summary": "The UAE real estate market...",
                        "confidence_score": 74.4,
                        "timestamp": "2026, 6, 3",
                        "duration_seconds": 131.49,
                        "error": None,
                    },
                    {
                        "id": "b9beb6f6-c40b-413c-9c57-9f33b76b23eb",
                        "query": "Failed query",
                        "summary": "",
                        "confidence_score": None,
                        "timestamp": "2026, 6, 3",
                        "duration_seconds": 5.2,
                        "error": "API timeout",
                    },
                ]
            }
        }
    )

    insights_history_list: list[InsightsHistoryItem] = Field(
        ..., description="List of insight history records", min_length=0
    )
