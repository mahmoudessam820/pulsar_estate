import time
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.scheduler.base import SchedulerBase
from app.scheduler.job_status import pipeline_job_status
from app.utils.redis_lock import acquire_lock, release_lock


class APSchedulerService(SchedulerBase):
    def __init__(self) -> None:
        self.scheduler = AsyncIOScheduler()

    def start(self) -> None:
        self.scheduler.start()

    def shutdown(self) -> None:
        self.scheduler.shutdown()

    # This function will edit before production,
    # we will use cron trigger instead of interval trigger to run the job at specific time
    def add_daily_job(self, func, minutes: int = 5) -> None:
        self.scheduler.add_job(
            self._run_with_lock,
            "interval",
            minutes=minutes,
            # CronTrigger(minutes=minutes),
            args=[func],
            id="interval_pipeline_job",
            replace_existing=True,
            misfire_grace_time=60,
        )

    async def _run_with_lock(self, func):
        locked = await acquire_lock()

        if not locked:
            print("Pipeline is currently locked. Skipping task execution.")
            return

        start_time = time.time()
        pipeline_job_status.last_run = datetime.now(timezone.utc)
        pipeline_job_status.last_error = None

        try:
            await func()

        except Exception as e:
            pipeline_job_status.last_error = str(e)
            raise

        finally:
            pipeline_job_status.last_duration = time.time() - start_time
            await release_lock()
