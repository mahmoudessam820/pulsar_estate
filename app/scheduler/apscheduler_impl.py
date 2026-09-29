import logging
from typing import Callable

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.scheduler.base import SchedulerBase
from app.utils.redis_lock import acquire_lock, release_lock, GLOBAL_PIPELINE_LOCK_KEY

logger = logging.getLogger(__name__)


class APSchedulerService(SchedulerBase):
    def __init__(
        self,
        db_session_factory: Callable,
        scheduled_query_repo_factory: Callable,
        pipeline_factory: Callable,
    ) -> None:
        self.scheduler = AsyncIOScheduler()
        self.db_session_factory = db_session_factory
        self.scheduled_query_repo_factory = scheduled_query_repo_factory
        self.pipeline_factory = pipeline_factory

    def start(self) -> None:
        # Schedule the processor to run every 1 minute
        self.scheduler.add_job(
            self._process_due_scheduled_queries,
            "interval",
            minutes=1,
            id="process_scheduled_queries_job",
            replace_existing=True,
            misfire_grace_time=60,  # Allow up to 60s delay if the scheduler is busy
        )
        self.scheduler.start()
        logger.info("Scheduled queries processor started (1-minute interval)")

    def shutdown(self) -> None:
        self.scheduler.shutdown()

    async def _process_due_scheduled_queries(self) -> None:
        """
        Fetches due scheduled queries, acquires the global lock, executes the pipeline,
        and updates the database state based on success or failure.
        """
        async with self.db_session_factory() as db:
            repo = self.scheduled_query_repo_factory(db)
            due_queries = await repo.get_due_queries()

            for query in due_queries:
                query_id_str = str(query.id)

                # 1. Check Global Lock First
                if not await acquire_lock(GLOBAL_PIPELINE_LOCK_KEY, ttl=600):
                    logger.info(
                        f"Global pipeline lock held. Skipping scheduled query {query_id_str} for this tick. It will be retried on the next tick."
                    )
                    continue  # Skip to the next query (all will be skipped if global lock is held)

                logger.info(
                    f"Starting execution of scheduled query {query_id_str} for user {query.user_id}"
                )
                pipeline = None
                try:
                    # 2. Execute Pipeline
                    pipeline = self.pipeline_factory(db)
                    await pipeline.run(query.query_text, user_id=str(query.user_id))

                    # 3. On Success: Mark as completed (is_active = False)
                    await repo.mark_as_completed(query_id_str)
                    logger.info(
                        f"Successfully completed scheduled query {query_id_str}"
                    )

                except Exception as e:
                    # 4. On Failure: Push back next_run_at to prevent infinite retry loops
                    logger.error(
                        f"Failed to execute scheduled query {query_id_str}: {str(e)}",
                        exc_info=True,
                    )
                    await repo.push_back_next_run(query_id_str, hours=24)

                finally:
                    # 5. Always release the global lock
                    await release_lock(GLOBAL_PIPELINE_LOCK_KEY)

                    # Ensure pipeline resources (like Crawl4AI browser) are cleaned up
                    if pipeline and hasattr(pipeline, "close"):
                        await pipeline.close()
