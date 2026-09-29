"""add foreign key to usage_tracking

Revision ID: 25c15299
Revises: 4ba7d335
Create Date: 2026-09-14 18:27:12
"""

from typing import Sequence, Union
from alembic import op

revision: str = "25c15299"
down_revision: Union[str, None] = "4ba7d335"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add the foreign key constraint to enforce referential integrity.
    op.create_foreign_key(
        "fk_usage_tracking_user_id",
        "usage_tracking",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_usage_tracking_user_id", "usage_tracking", type_="foreignkey"
    )
