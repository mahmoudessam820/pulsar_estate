import logging
from typing import List
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from datetime import datetime, time, timedelta, timezone

from app.data.models.scheduled_queries import ScheduledQuery
from app.data.repositories.base import ScheduledQueryRepositoryBase

logger = logging.getLogger(__name__)


class ScheduledQueryService:
    def __init__(self, scheduled_query_repo: ScheduledQueryRepositoryBase):
        self.scheduled_query_repo = scheduled_query_repo

    def _parse_12_hour_time(self, time_str: str) -> time:
        """
        Converts a 12-hour time string (e.g., '08:20 PM', '8:20 AM', '12:00 PM')
        into a standard 24-hour datetime.time object.
        """
        try:
            # %I = 12-hour clock (01-12), %M = minute, %p = AM/PM
            # .strip() handles accidental spaces like " 8:20 PM "
            parsed_dt = datetime.strptime(time_str.strip(), "%I:%M %p")
            return parsed_dt.time()
        except ValueError:
            raise ValueError(
                f"Invalid time format. Expected 12-hour format like '08:20 AM' or '8:20 PM', got '{time_str}'"
            )

    def _calculate_next_run(self, execution_time: time, timezone_str: str) -> datetime:
        """
        UNIVERSAL: Calculates the next run time in UTC, respecting ANY valid IANA timezone.
        Handles Daylight Saving Time automatically.
        """
        try:
            # 1. Resolve the user's timezone safely
            try:
                user_tz = ZoneInfo(timezone_str)
            except ZoneInfoNotFoundError:
                logger.warning(
                    f"Invalid timezone '{timezone_str}', falling back to UTC"
                )
                user_tz = timezone.utc

            # 2. Get current time in the user's specific timezone
            now_in_user_tz = datetime.now(user_tz)

            # 3. Combine today's date (in user's timezone) with the requested execution time
            next_run_in_user_tz = datetime.combine(
                now_in_user_tz.date(), execution_time, tzinfo=user_tz
            )

            # 4. If the time has already passed today in the user's timezone, schedule for tomorrow
            if next_run_in_user_tz <= now_in_user_tz:
                next_run_in_user_tz += timedelta(days=1)

            # 5. Convert to UTC for safe, consistent database storage
            return next_run_in_user_tz.astimezone(timezone.utc)

        except Exception as e:
            logger.error(f"Error calculating next run time: {str(e)}", exc_info=True)
            raise

    async def create_scheduled_query(
        self,
        user_id: str,
        query_text: str,
        execution_time_str: str,
        timezone: str = "UTC",
    ) -> ScheduledQuery:
        """
        Create a new scheduled query for the user.
        Now accepts a 12-hour string like "08:20 PM".
        """
        try:
            # 1. Parse the user-friendly string into a 24-hour time object
            execution_time = self._parse_12_hour_time(execution_time_str)

            # 2. Calculate next run (your existing, proven logic)
            next_run_at = self._calculate_next_run(execution_time, timezone)

            # 3. Save to DB
            new_query = await self.scheduled_query_repo.create(
                user_id=user_id,
                query_text=query_text,
                execution_time=execution_time,
                timezone=timezone,
                next_run_at=next_run_at,
            )

            logger.info(
                f"Created scheduled query {new_query.id} for user {user_id} at {execution_time_str}"
            )
            return new_query
        except ValueError as ve:
            logger.warning(f"ValueError while creating scheduled query: {str(ve)}")
            raise

    async def list_scheduled_queries(self, user_id: str) -> List[ScheduledQuery]:
        """List all scheduled queries for a given user."""
        return await self.scheduled_query_repo.get_by_user(user_id)

    async def toggle_scheduled_query(
        self, user_id: str, query_id: str, is_active: bool
    ) -> None:
        """Toggle the active status of a scheduled query."""

        # Verify ownership
        query = await self.scheduled_query_repo.get_by_id(query_id)
        if not query:
            raise ValueError("Scheduled query not found")

        if str(query.user_id) != user_id:
            raise PermissionError("You do not have permission to modify this query")

        await self.scheduled_query_repo.toggle_active(query_id, is_active)
        logger.info(f"Toggled scheduled query {query_id} to is_active={is_active}")

    async def delete_scheduled_query(self, user_id: str, query_id: str) -> None:
        """Delete a scheduled query for a user."""

        # Verify ownership
        query = await self.scheduled_query_repo.get_by_id(query_id)
        if not query:
            raise ValueError("Scheduled query not found")

        if str(query.user_id) != user_id:
            raise PermissionError("You do not have permission to delete this query")

        await self.scheduled_query_repo.delete(query_id)
        logger.info(f"Deleted scheduled query {query_id}")
