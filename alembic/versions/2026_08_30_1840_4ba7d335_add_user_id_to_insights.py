"""add user_id to insights safely

Revision ID: 4ba7d335
Revises: 9919a5dcf6ee
Create Date: 2026-08-30 18:40:49
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "4ba7d335"
down_revision: Union[str, None] = "9919a5dcf6ee"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add user_id column (Must be nullable=True initially to preserve existing rows)
    op.add_column(
        "insights", sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True)
    )

    # 2. Create foreign key constraint safely
    op.create_foreign_key(
        "fk_insights_user_id",
        "insights",
        "users",
        ["user_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    # Reverse operations in exact opposite order
    op.drop_constraint("fk_insights_user_id", "insights", type_="foreignkey")
    op.drop_column("insights", "user_id")
