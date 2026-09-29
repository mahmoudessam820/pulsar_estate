import uuid
import logging
from typing import List
from datetime import date, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.data.repositories.base import UsageRepositoryBase
from app.data.models.usage_tracking import UsageTracking

logger = logging.getLogger(__name__)


class PostgresUsageRepository(UsageRepositoryBase):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def count_today(
        self, user_id: str, metric_type: str = "on_demand_run"
    ) -> int:
        """Count usage for today for a specific metric type."""
        try:
            today = date.today()
            stmt = select(UsageTracking).where(
                UsageTracking.user_id == uuid.UUID(str(user_id)),
                UsageTracking.usage_date == today,
                UsageTracking.metric_type == metric_type,
            )
            result = await self.db.execute(stmt)
            record = result.scalar_one_or_none()

            return record.count if record else 0
        except ValueError:
            logger.warning(f"Invalid UUID format for user_id: {user_id}")
            return 0
        except Exception as e:
            logger.error(
                f"Failed to count usage for user {user_id}: {str(e)}", exc_info=True
            )
            raise

    async def increment(self, user_id: str, metric_type: str = "on_demand_run") -> None:
        """
        Increment usage count for today using atomic UPSERT.
        This prevents race conditions when multiple requests arrive simultaneously.
        """
        try:
            today = date.today()
            user_uuid = uuid.UUID(str(user_id))

            # PostgreSQL UPSERT: INSERT ... ON CONFLICT DO UPDATE
            stmt = (
                pg_insert(UsageTracking)
                .values(
                    user_id=user_uuid,
                    usage_date=today,
                    metric_type=metric_type,
                    count=1,
                )
                .on_conflict_do_update(
                    index_elements=["user_id", "usage_date", "metric_type"],
                    set_={"count": UsageTracking.count + 1, "updated_at": func.now()},
                )
            )

            await self.db.execute(stmt)
            await self.db.commit()
            logger.info(f"Incremented {metric_type} usage for user {user_id}")
        except ValueError:
            logger.warning(f"Invalid UUID format for user_id: {user_id}")
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(
                f"Failed to increment usage for user {user_id}: {str(e)}", exc_info=True
            )
            raise

    async def get_usage_history(
        self, user_id: str, metric_type: str, days: int = 30
    ) -> List[UsageTracking]:
        """Get usage history for the last N days."""
        try:
            start_date = date.today() - timedelta(days=days)
            stmt = (
                select(UsageTracking)
                .where(
                    UsageTracking.user_id == uuid.UUID(str(user_id)),
                    UsageTracking.metric_type == metric_type,
                    UsageTracking.usage_date >= start_date,
                )
                .order_by(UsageTracking.usage_date.desc())
            )

            result = await self.db.execute(stmt)
            return result.scalars().all()
        except ValueError:
            logger.warning(f"Invalid UUID format for user_id: {user_id}")
            return []
        except Exception as e:
            logger.error(
                f"Failed to get usage history for user {user_id}: {str(e)}",
                exc_info=True,
            )
            raise
