from fastapi import APIRouter
from app.scheduler.job_status import pipeline_job_status

router = APIRouter(prefix="/scheduler", tags=["Scheduler"])


@router.get("/status")
async def get_scheduler_status():
    return {
        "last_run": pipeline_job_status.last_run,
        "last_duration_seconds": pipeline_job_status.last_duration,
        "last_error": pipeline_job_status.last_error,
    }
