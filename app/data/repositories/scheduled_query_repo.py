import uuid
import logging
from typing import List
from datetime import datetime, timedelta, time

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func

from app.data.repositories.base import ScheduledQueryRepositoryBase
from app.data.models.scheduled_queries import ScheduledQuery

logger = logging.getLogger(__name__)


class PostgresScheduledQueryRepository(ScheduledQueryRepositoryBase):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        user_id: str,
        query_text: str,
        execution_time: time,
        timezone: str = "UTC",
        next_run_at: datetime = None,
    ) -> ScheduledQuery:
        """Create a new scheduled query."""
        try:
            user_uuid = uuid.UUID(user_id)

            # If next_run_at not provided, calculate based on execution_time
            if next_run_at is None:
                now = datetime.now()
                next_run_at = datetime.combine(now.date(), execution_time)
                if next_run_at <= now:
                    # If time has passed today, schedule for tomorrow
                    next_run_at = next_run_at.replace(day=now.day + 1)

            new_query = ScheduledQuery(
                user_id=user_uuid,
                query_text=query_text,
                execution_time=execution_time,
                timezone=timezone,
                next_run_at=next_run_at,
            )

            self.db.add(new_query)
            await self.db.commit()
            await self.db.refresh(new_query)
            logger.info(f"Created scheduled query {new_query.id} for user {user_id}")
            return new_query
        except ValueError:
            logger.warning(f"Invalid UUID format for user_id: {user_id}")
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to create scheduled query: {str(e)}", exc_info=True)
            raise

    async def get_by_user(self, user_id: str) -> List[ScheduledQuery]:
        """Get all scheduled queries for a user."""
        try:
            stmt = (
                select(ScheduledQuery)
                .where(ScheduledQuery.user_id == uuid.UUID(user_id))
                .order_by(ScheduledQuery.created_at.desc())
            )

            result = await self.db.execute(stmt)
            return result.scalars().all()
        except ValueError:
            logger.warning(f"Invalid UUID format for user_id: {user_id}")
            return []
        except Exception as e:
            logger.error(
                f"Failed to get scheduled queries for user {user_id}: {str(e)}",
                exc_info=True,
            )
            raise

    async def get_by_id(self, query_id: str) -> List[ScheduledQuery]:
        """Get a specific scheduled query by ID."""
        try:
            stmt = select(ScheduledQuery).where(
                ScheduledQuery.id == uuid.UUID(query_id)
            )
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
        except ValueError:
            logger.warning(f"Invalid UUID format for query_id: {query_id}")
            return None
        except Exception as e:
            logger.error(
                f"Failed to get scheduled query {query_id}: {str(e)}", exc_info=True
            )
            raise

    async def get_due_queries(self) -> List[ScheduledQuery]:
        """Get all queries where next_run_at <= func.now() and is_active = true."""
        try:
            stmt = (
                select(ScheduledQuery)
                .where(
                    ScheduledQuery.is_active == True,
                    ScheduledQuery.next_run_at <= func.now(),
                )
                .order_by(ScheduledQuery.next_run_at.asc())
            )

            result = await self.db.execute(stmt)
            queries = result.scalars().all()

            logger.info(f"Found {len(queries)} due scheduled queries")
            return queries
        except Exception as e:
            logger.error(f"Failed to get due queries: {str(e)}", exc_info=True)
            raise

    async def update_next_run(self, query_id: str, next_run_at: datetime) -> None:
        """Update the next_run_at timestamp after execution."""
        try:
            stmt = (
                update(ScheduledQuery)
                .where(ScheduledQuery.id == uuid.UUID(query_id))
                .values(
                    next_run_at=next_run_at,
                    last_run_at=datetime.now(),
                    updated_at=datetime.now(),
                )
            )

            await self.db.execute(stmt)
            await self.db.commit()
            logger.info(f"Updated next_run_at for scheduled query {query_id}")
        except ValueError:
            logger.warning(f"Invalid UUID format for query_id: {query_id}")
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(
                f"Failed to update next_run_at for query {query_id}: {str(e)}",
                exc_info=True,
            )
            raise

    async def toggle_active(self, query_id: str, is_active: bool) -> None:
        """Pause or resume a scheduled query."""
        try:
            stmt = (
                update(ScheduledQuery)
                .where(ScheduledQuery.id == uuid.UUID(query_id))
                .values(is_active=is_active, updated_at=datetime.now())
            )

            await self.db.execute(stmt)
            await self.db.commit()
            logger.info(f"Toggled scheduled query {query_id} to is_active={is_active}")
        except ValueError:
            logger.warning(f"Invalid UUID format for query_id: {query_id}")
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to toggle query {query_id}: {str(e)}", exc_info=True)
            raise

    async def delete(self, query_id: str) -> None:
        """Delete a scheduled query."""
        try:
            stmt = delete(ScheduledQuery).where(
                ScheduledQuery.id == uuid.UUID(query_id)
            )

            await self.db.execute(stmt)
            await self.db.commit()
            logger.info(f"Deleted scheduled query {query_id}")
        except ValueError:
            logger.warning(f"Invalid UUID format for query_id: {query_id}")
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to delete query {query_id}: {str(e)}", exc_info=True)
            raise

    async def count_active_by_user(self, user_id: str) -> int:
        """Count active scheduled queries for a user (for quota enforcement)."""
        try:
            stmt = select(func.count()).where(
                ScheduledQuery.user_id == uuid.UUID(user_id),
                ScheduledQuery.is_active == True,
            )

            result = await self.db.execute(stmt)
            return result.scalar() or 0
        except ValueError:
            logger.warning(f"Invalid UUID format for user_id: {user_id}")
            return 0
        except Exception as e:
            logger.error(
                f"Failed to count active queries for user {user_id}: {str(e)}",
                exc_info=True,
            )
            raise

    async def mark_as_completed(self, query_id: str) -> None:
        """
        Marks a scheduled query as completed (is_active = False).
        It will never be fetched by get_due_queries() again.
        """
        try:
            stmt = (
                update(ScheduledQuery)
                .where(ScheduledQuery.id == uuid.UUID(query_id))
                .values(is_active=False, updated_at=datetime.now())
            )
            await self.db.execute(stmt)
            await self.db.commit()
            logger.info(
                f"Marked scheduled query {query_id} as completed (is_active=False)"
            )
        except Exception as e:
            await self.db.rollback()
            logger.error(
                f"Failed to mark query {query_id} as completed: {str(e)}", exc_info=True
            )
            raise

    async def push_back_next_run(self, query_id: str, hours: int = 24) -> None:
        """
        Handles execution failure by pushing the next_run_at time into the future.
        This prevents infinite retry loops on the next 1-minute scheduler tick,
        while keeping is_active=True so the user can see it's still scheduled.
        """
        try:
            next_run = datetime.now() + timedelta(hours=hours)
            stmt = (
                update(ScheduledQuery)
                .where(ScheduledQuery.id == uuid.UUID(query_id))
                .values(next_run_at=next_run, updated_at=datetime.now())
            )
            await self.db.execute(stmt)
            await self.db.commit()
            logger.warning(
                f"Pushed back failed scheduled query {query_id} by {hours} hours"
            )
        except Exception as e:
            await self.db.rollback()
            logger.error(
                f"Failed to push back query {query_id}: {str(e)}", exc_info=True
            )
            raise
