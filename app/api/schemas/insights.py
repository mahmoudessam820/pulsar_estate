import uuid
from datetime import datetime
from typing import Literal, Any

from pydantic import BaseModel, Field, HttpUrl, ConfigDict, model_validator


# Nested Models


class EvidenceItem(BaseModel):
    """A single piece of evidence supporting an insight claim"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "claim": "Dubai recorded record transactions in 2025",
                "source_url": "https://example.com/report",
            }
        }
    )
    claim: str = Field(..., description="The factual claim being made")
    source_url: HttpUrl = Field(..., description="URL to the source document")


class ConfidenceMetrics(BaseModel):
    """Confidence scoring breakdown for the insight"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "score": 66.2,
                "label": "Moderate",
                "badge": "🟡",
                "source_strength": 0.5,
                "evidence_coverage": 1.0,
                "freshness": 0.31,
                "consensus": 1.0,
                "sources_count": 15,
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
        ..., description="Emoji badge for UI display", examples=["🔴", "🟡", "🟢"]
    )
    source_strength: float = Field(
        ..., ge=0, le=1, description="Authority score of sources"
    )
    evidence_coverage: float = Field(
        ..., ge=0, le=1, description="How well claims are supported"
    )
    freshness: float = Field(
        ..., ge=0, le=1, description="Recency score of source data"
    )
    consensus: float = Field(
        ..., ge=0, le=1, description="Agreement level across sources"
    )
    sources_count: int = Field(..., ge=0, description="Number of sources analyzed")


class InsightContent(BaseModel):
    """The core insight analysis and findings"""

    model_config = ConfigDict(
        from_attributes=True, extra="allow"
    )  # extra="allow" prevents breaking if AI adds new fields

    summary: str = Field(
        ..., description="Executive summary of the insight", max_length=5000
    )
    key_trends: list[str] = Field(
        ..., description="List of key market trends identified", min_length=1
    )
    market_sentiment: Literal["negative", "neutral", "positive", "mixed"] = Field(
        ..., description="Overall market sentiment"
    )
    evidence: list[EvidenceItem] = Field(
        ..., description="Supporting evidence for claims"
    )
    confidence: ConfidenceMetrics = Field(
        ..., description="Confidence scoring breakdown"
    )
    confidence_explanation: str = Field(
        ..., description="Plain-language explanation of confidence rating"
    )


# Response Schema


class InsightResponse(BaseModel):
    """Complete insight response returned by /insights/latest"""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "0192a3b4-c5d6-7e8f-9a0b-1c2d3e4f5a6b",
                "created_at": "2026-07-19T10:00:00Z",
                "query": "Dubai Luxury Residential Real Estate Market",
                "documents_collected": 15,
                "insights": {},
                "sources": ["https://example.com"],
            }
        },
    )

    # Database traceability fields
    id: uuid.UUID = Field(..., description="Unique identifier for this insight")
    created_at: datetime = Field(..., description="When this insight was generated")

    # Core fields
    query: str = Field(
        ..., description="Original search query that generated this insight"
    )
    documents_collected: int = Field(
        ..., ge=0, description="Number of documents analyzed"
    )
    insights: InsightContent = Field(..., description="The generated insight analysis")
    sources: list[HttpUrl] = Field(
        ..., description="List of source URLs used in analysis"
    )

    @model_validator(mode="before")
    @classmethod
    def map_db_model_to_response(cls, data: Any) -> Any:
        """
        Intercepts the SQLAlchemy Insight model and maps the 'raw_ai_output' JSONB column
        to the nested 'insights' field expected by the API schema.
        """
        if hasattr(data, "raw_ai_output"):
            return {
                "id": data.id,
                "created_at": data.created_at,
                "query": data.query,
                "documents_collected": data.documents_collected,
                "insights": data.raw_ai_output,  # Maps JSONB -> Nested Pydantic Model
                "sources": data.sources,
            }
        return data
