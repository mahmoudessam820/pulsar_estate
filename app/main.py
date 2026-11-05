from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from slowapi.errors import RateLimitExceeded

from app.core.database import AsyncSessionLocal
from app.core.pipeline.factory import build_pipeline
from app.data.repositories.scheduled_query_repo import PostgresScheduledQueryRepository
from app.scheduler.apscheduler_impl import APSchedulerService
from app.core.limiter import limiter
from app.config.settings import settings
from app.utils.logging import setup_logging
from app.core.celery_app import (
    celery_app,
)  # Import the Celery app to ensure it's initialized
from app.api.routes import (
    health,
    insights,
    scheduled_queries,
    admin,
    auth,
    integrations,
    pipeline,
    billing,
    events,
)


setup_logging(settings.log_level)


def _rate_limit_exceeded_handler(
    request: Request, exc: RateLimitExceeded
) -> JSONResponse:
    """Custom JSON response for rate limit violations, ensuring API consistency."""
    return JSONResponse(
        status_code=429,
        content={
            "error": "Rate Limit Exceeded",
            "detail": str(exc.detail),
        },
        headers={"Retry-After": "60"},  # Standard hint for clients
    )


# Global scheduler instance
scheduler_service: APSchedulerService | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages the application lifecycle, including starting and stopping
    the background scheduler for user-scheduled queries.
    """
    global scheduler_service

    # 1. Define factories for the scheduler to avoid circular imports
    def get_scheduled_query_repo(db):
        return PostgresScheduledQueryRepository(db)

    def get_pipeline(db):
        return build_pipeline(db=db)

    # 2. Initialize and start the scheduler
    scheduler_service = APSchedulerService(
        db_session_factory=AsyncSessionLocal,
        scheduled_query_repo_factory=get_scheduled_query_repo,
        pipeline_factory=get_pipeline,
    )
    scheduler_service.start()

    yield  # Application is running and serving requests

    # 3. Gracefully shutdown the scheduler on app exit
    if scheduler_service:
        scheduler_service.shutdown()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.api_version,
        lifespan=lifespan,
    )

    # Limiter and exception handler setup
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # Include API routes
    app.include_router(admin.router)
    app.include_router(health.router)
    app.include_router(insights.router)
    app.include_router(scheduled_queries.router)
    app.include_router(auth.router)
    app.include_router(integrations.router)
    app.include_router(pipeline.router)
    app.include_router(billing.router)
    app.include_router(events.router)

    return app


app = create_app()
