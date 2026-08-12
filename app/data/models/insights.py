import uuid
from datetime import datetime

from uuid_utils import uuid7
from sqlalchemy import String, Integer, DateTime, Text, func, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Insights(Base):
    __tablename__ = "insights"

    # Primary Key: UUIDv7
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid7
    )

    # Core Query Metadata
    query: Mapped[str] = mapped_column(String(1000), nullable=False, index=True)
    documents_collected: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Flattened fields for easy querying and indexing
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    confidence_label: Mapped[str] = mapped_column(String(50), nullable=False)
    confidence_explanation: Mapped[str | None] = mapped_column(Text, nullable=True)

    # JSONB fields for flexible AI output and sources array
    # raw_ai_output stores the entire nested "insights" object from the AI response
    raw_ai_output: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    sources: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,  # Indexed for time range-related queries and cache validity checks
    )
