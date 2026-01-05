from fastapi import FastAPI

from app.config.settings import settings
from app.utils.logging import setup_logging


setup_logging(settings.log_level)

app = FastAPI(
    title=settings.app_name,
    version=settings.api_version,
)


@app.get("/health")
def check_health():
    return {"status": "ok"}
