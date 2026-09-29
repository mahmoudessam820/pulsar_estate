import uuid
from datetime import datetime

from uuid_utils import uuid7
from sqlalchemy import String, Boolean, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ApiKey(Base):
    __tablename__ = "api_keys"

    # Primary Key: UUIDv7
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid7
    )

    # Foreign Key to users table (CASCADE on delete)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Key Metadata
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    hashed_key: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    prefix: Mapped[str] = mapped_column(String(10), nullable=False)

    # Status & Usage
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
