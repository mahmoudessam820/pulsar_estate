import uuid
from datetime import datetime

from uuid_utils import uuid7
from sqlalchemy import String, Text, Float, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    # Primary Key: UUIDv7
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid7
    )

    # Foreign Keys (both nullable for flexibility)
    # insight_id: NULL if pipeline failed before saving insight
    insight_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("insights.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    # user_id: NULL if triggered by system/admin global pipeline
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Execution Status
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # 'pending', 'running', 'success', 'failed'

    # Error Details (populated only if status = 'failed')
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Performance Metrics
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Timestamps
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
