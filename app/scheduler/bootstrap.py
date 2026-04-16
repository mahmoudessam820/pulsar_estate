from app.scheduler.apscheduler_impl import APSchedulerService
from app.core.pipeline.pipeline_tasks import run_daily_pipeline


scheduler = APSchedulerService()


async def start_scheduler():
    scheduler.add_daily_job(run_daily_pipeline, minutes=5)
    scheduler.start()


async def shutdown_scheduler():
    scheduler.shutdown()
