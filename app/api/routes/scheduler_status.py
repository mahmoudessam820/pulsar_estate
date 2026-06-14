from fastapi import APIRouter

from app.scheduler.job_status import pipeline_job_status
from app.api.schemas import SchedulerStatusResponse


router = APIRouter(prefix="/scheduler", tags=["Scheduler Status"])


@router.get(
    "/status",
    response_model=SchedulerStatusResponse,
    summary="Get scheduler status",
    description="Returns the status of the last pipeline scheduler run, including timestamp, duration, and any errors.",
)
async def get_scheduler_status():
    return SchedulerStatusResponse(
        last_run=pipeline_job_status.last_run,
        last_duration_seconds=pipeline_job_status.last_duration,
        last_error=pipeline_job_status.last_error,
    )
