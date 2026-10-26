"""add semantic caching columns to insights

Revision ID: 990be311
Revises: 25c15299
Create Date: 2026-10-15 20:41:57
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from app.config.settings import settings

revision: str = "990be311"
down_revision: Union[str, None] = "25c15299"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Ensure the pgvector extension is enabled in PostgreSQL
    # This is safe to run multiple times; it does nothing if the extension already exists.
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # 2. Add query_embedding column for semantic caching
    op.add_column(
        "insights",
        sa.Column(
            "query_embedding", Vector(settings.embedding_dimension), nullable=True
        ),
    )

    # 3. Add cache_expires_at column
    op.add_column(
        "insights",
        sa.Column("cache_expires_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    # Reverse operations in exact opposite order
    op.drop_column("insights", "cache_expires_at")
    op.drop_column("insights", "query_embedding")

    # Note: We intentionally do NOT drop the 'vector' extension here.
    # Dropping extensions can be dangerous if other tables or future features rely on it.
