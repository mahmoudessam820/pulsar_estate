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
    # Give the local model enough time to complete the full Map-Reduce pipeline without being prematurely killed.
    # You can adjust this value based on your specific model and hardware capabilities may be necessary. 
    # For example, if your model takes longer than 30 minutes to process a single request, you may need to increase this value,
    # but this very large time is not accepted in the real world.
    # If you will use cloud-hosted LLMs, you can reduce this value to something more reasonable like 60 seconds.
    task_time_limit=1800,  # Hard timeout of (30 minutes) for local LLMs.
)
