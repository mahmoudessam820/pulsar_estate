"""add is_cached flag to pipeline_runs

Revision ID: ff477a71
Revises: 990be311
Create Date: 2026-10-15 21:07:08
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "ff477a71"
down_revision: Union[str, None] = "990be311"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add is_cached column.
    # CRITICAL: We use server_default=sa.text('false') because the column is NOT NULL.
    # Without a server default, PostgreSQL would reject adding a NOT NULL column to a table
    # that already contains rows. The server default safely backfills all existing rows with 'false'.
    op.add_column(
        "pipeline_runs",
        sa.Column(
            "is_cached", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
    )


def downgrade() -> None:
    op.drop_column("pipeline_runs", "is_cached")
