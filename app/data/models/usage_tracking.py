import uuid
from datetime import datetime, date

from uuid_utils import uuid7
from sqlalchemy import (
    String,
    Integer,
    Date,
    DateTime,
    func,
    UniqueConstraint,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class UsageTracking(Base):
    __tablename__ = "usage_tracking"

    # Primary Key: UUIDv7
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid7
    )

    # Foreign Key to users table
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Date-based aggregation
    usage_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    # Type of usage (e.g., 'on_demand_run', 'scheduled_run', 'api_call')
    metric_type: Mapped[str] = mapped_column(String(50), nullable=False)

    # Count for this user/date/metric combination
    count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Composite unique constraint for UPSERT operations
    __table_args__ = (
        UniqueConstraint(
            "user_id", "usage_date", "metric_type", name="uq_usage_user_date_metric"
        ),
    )
