import uuid
import redis.asyncio as redis

# Initialize Redis client
redis_client = redis.Redis(host="localhost", port=6379, decode_responses=True)

# Global lock key to prevent concurrent AI-intensive pipeline executions
GLOBAL_PIPELINE_LOCK_KEY = "lock:global_pipeline_execution"


async def acquire_lock(lock_key: str, ttl: int = 600) -> bool:
    """
    Acquire a distributed lock for a specific key.
    ttl: Time-to-live in seconds (default 600s = 10 mins, safely covering 2-4 min executions).
    Returns True if lock acquired, False if already locked.
    """
    token = str(uuid.uuid4())

    # nx=True ensures we only set the key if it does not already exist
    result = await redis_client.set(lock_key, token, nx=True, ex=ttl)
    return bool(result)


async def release_lock(lock_key: str) -> None:
    """
    Release the distributed lock for a specific key.
    """
    await redis_client.delete(lock_key)
