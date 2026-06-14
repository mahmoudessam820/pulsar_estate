import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl, ConfigDict, field_validator


# Custom Validators


def parse_unusual_date(value: str) -> datetime:
    """
    Parse date strings like "2026, 4, 7" → datetime
    Adjust this function if your date format varies
    """
    if isinstance(value, datetime):
        return value
    # Match "YYYY, M, D" or "YYYY, MM, DD"
    match = re.match(r"(\d{4}),\s*(\d{1,2}),\s*(\d{1,2})", str(value))
    if match:
        year, month, day = map(int, match.groups())
        return datetime(year, month, day)
    # Fallback: try ISO format
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


# Nested Models


class ConfidenceMetrics(BaseModel):
    """Confidence scoring for topic version"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "score": 81.8,
                "label": "High",
                "badge": "🟢",
                "source_strength": 0.65,
                "evidence_coverage": 1.0,
                "freshness": 0.79,
                "consensus": 1.0,
                "sources_count": 14,
            }
        }
    )

    score: float = Field(
        ..., ge=0, le=100, description="Overall confidence score (0-100)"
    )
    label: Literal["Low", "Moderate", "High"] = Field(
        ..., description="Human-readable confidence level"
    )
    badge: str = Field(
        ..., description="Emoji badge for UI", examples=["🔴", "🟡", "🟢"]
    )

    source_strength: float = Field(
        ..., ge=0, le=1, description="Source authority score"
    )
    evidence_coverage: float = Field(
        ..., ge=0, le=1, description="Evidence support ratio"
    )
    freshness: float = Field(..., ge=0, le=1, description="Data recency score")
    consensus: float = Field(..., ge=0, le=1, description="Source agreement level")

    sources_count: int = Field(..., ge=0, description="Number of sources analyzed")


class TopicVersion(BaseModel):
    """Version metadata for an insight topic"""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={"example": {"id": "uuid", "version": 1, "summary": "..."}},
    )

    id: str = Field(..., description="Unique version identifier (UUID)")
    topic_id: str = Field(..., description="Parent topic identifier (UUID)")
    version: int = Field(..., ge=1, description="Version number")
    summary: str = Field(
        ..., description="Executive summary of this version", max_length=5000
    )
    confidence: ConfidenceMetrics = Field(..., description="Confidence metrics")
    sources: list[HttpUrl] = Field(..., description="Source URLs used for this version")
    created_at: datetime = Field(..., description="When this version was created")

    # Auto-parse the unusual date format
    @field_validator("created_at", mode="before")
    @classmethod
    def parse_created_at(cls, value):
        return parse_unusual_date(value)


class TopicItem(BaseModel):
    """A single insight topic"""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Topic identifier (UUID)")
    topic: str = Field(..., description="Topic title/query", max_length=1000)

    created_at: datetime = Field(..., description="When topic was created")

    @field_validator("created_at", mode="before")
    @classmethod
    def parse_created_at(cls, value):
        return parse_unusual_date(value)


# Main Response Schema


class InsightTopicResponse(BaseModel):
    """Response for /insight-topics/latest/{topic_id}"""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "version": {
                    "id": "9f288847-0000-0000-0000-000000000000",
                    "topic_id": "a5a4bacd-0000-0000-0000-000000000000",
                    "version": 1,
                    "summary": "Dubai's real estate market is showing steady growth.",
                    "confidence": {
                        "score": 81.8,
                        "label": "High",
                        "badge": "🟢",
                        "source_strength": 0.65,
                        "evidence_coverage": 1.0,
                        "freshness": 0.79,
                        "consensus": 1.0,
                        "sources_count": 14,
                    },
                    "sources": ["https://example.com/report"],
                    "created_at": "2026-04-07T00:00:00",
                },
                "topics": [
                    {
                        "id": "a5a4bacd-0000-0000-0000-000000000000",
                        "topic": "Dubai Luxury Properties",
                        "created_at": "2026-04-07T00:00:00",
                    }
                ],
            }
        },
    )

    version: TopicVersion = Field(
        ..., description="Latest version metadata for the topic"
    )
    topics: list[TopicItem] = Field(
        ..., description="List of related topics", min_length=1
    )
