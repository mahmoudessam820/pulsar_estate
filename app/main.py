from fastapi import FastAPI

from app.config.settings import settings
from app.utils.logging import setup_logging
from app.api.routes import (
    health,
    insights,
    scheduler,
    admin,
    insights_history,
    insight_topic,
    auth,
    pipeline,
)
from app.scheduler.bootstrap import start_scheduler, shutdown_scheduler


setup_logging(settings.log_level)


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.api_version,
    )

    # Include API routes
    app.include_router(admin.router)
    app.include_router(health.router)
    app.include_router(insights.router)
    app.include_router(scheduler.router)
    app.include_router(insights_history.router)
    app.include_router(insight_topic.router)
    app.include_router(auth.router)
    app.include_router(pipeline.router)

    # Scheduler setup
    @app.on_event("startup")
    async def startup_event():
        await start_scheduler()

    @app.on_event("shutdown")
    async def shutdown_event():
        await shutdown_scheduler()

    return app


app = create_app()
