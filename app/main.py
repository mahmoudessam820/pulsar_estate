from fastapi import FastAPI

from app.config.settings import settings
from app.utils.logging import setup_logging
from app.api.routes import health

setup_logging(settings.log_level)


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.api_version,
    )

    app.include_router(health.router)

    return app


app = create_app()
