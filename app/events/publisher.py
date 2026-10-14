import logging

import redis

from app.config.settings import settings
from app.api.schemas.events import TaskCompletionEvent


logger = logging.getLogger(__name__)

# Sync redis client for Celery workers
redis_client = redis.Redis(
    host=settings.redis_host, port=settings.redis_port, decode_responses=True
)


def publish_task_update(
    user_id: str,
    task_id: str,
    status: str,
    insight_id: str | None = None,
    error: str | None = None,
):
    """
    Validates the payload using Pydantic, then publishes the task completion
    event to Redis for the specific user.
    """
    try:
        # 1. Use the schema to validate and construct the payload
        event = TaskCompletionEvent(
            task_id=task_id, status=status, insight_id=insight_id, error=error
        )

        # 2. Serialize the validated model to JSON
        payload = event.model_dump_json()

        # 3. Publish to Redis
        channel = f"task_updates:{user_id}"
        redis_client.publish(channel, payload)
        logger.info(f"Published task update for user {user_id}, task {task_id}")

    except Exception as e:
        logger.error(f"Failed to validate or publish task update to Redis: {e}")
        raise
