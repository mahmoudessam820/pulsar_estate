import uuid

import redis
import redis.asyncio as async_redis

from app.config.settings import settings


# Initialize Redis client dynamically using settings
sync_redis_client = redis.Redis(
    host=settings.redis_host, port=settings.redis_port, decode_responses=True
)


# 2. Lazy async client (safe for FastAPI, binds to the currently running event loop)
_async_client = None


def get_async_redis_client():
    global _async_client
    if _async_client is None:
        _async_client = async_redis.Redis(
            host=settings.redis_host, port=settings.redis_port, decode_responses=True
        )
    return _async_client


# Global lock key to prevent concurrent AI-intensive pipeline executions
GLOBAL_PIPELINE_LOCK_KEY = "lock:global_pipeline_execution"


# Async Functions (for FastAPI)
async def acquire_lock(lock_key: str, ttl: int = 600) -> bool:
    client = get_async_redis_client()
    token = str(uuid.uuid4())
    result = await client.set(lock_key, token, nx=True, ex=ttl)
    return bool(result)


async def release_lock(lock_key: str) -> None:
    client = get_async_redis_client()
    await client.delete(lock_key)


# Sync Functions (for Celery)
def acquire_lock_sync(lock_key: str, ttl: int = 600) -> bool:
    token = str(uuid.uuid4())
    result = sync_redis_client.set(lock_key, token, nx=True, ex=ttl)
    return bool(result)


def release_lock_sync(lock_key: str) -> None:
    sync_redis_client.delete(lock_key)
