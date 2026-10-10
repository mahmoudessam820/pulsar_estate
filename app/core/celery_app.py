import os

from celery import Celery

from app.config.settings import settings

# Set default Django settings module for the 'celery' program (not used here, but good practice)
os.environ.setdefault("CELERY_CONFIG_MODULE", "app.config.settings")


# Initialize Celery app
celery_app = Celery(
    "pulsar_estate",
    broker=settings.celery_broker_url,
    backend="disabled",  # Use pipeline_runs table as the single source of truth
    include=["app.core.pipeline.tasks"],
)

# Configure Celery defaults
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,  # Hard timeout of 10 minutes for safety
)
