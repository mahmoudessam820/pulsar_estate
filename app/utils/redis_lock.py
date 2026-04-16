import uuid

import redis.asyncio as redis


redis_client = redis.Redis(host="localhost", port=6379, decode_responses=True)

PIPLEINE_LOCK_KEY = "pipeline:daily_lock"
# Time to live for the lock in seconds (e.g., 1 hour) to prevent stale locks in case of failures
LOCK_TTL = 3600

lock_token = None


async def acquire_lock():
    global lock_token

    token = str(uuid.uuid4())

    result = await redis_client.set(PIPLEINE_LOCK_KEY, "locked", nx=True, ex=LOCK_TTL)

    if result:
        lock_token = token
        return True

    return False


async def release_lock():
    global lock_token

    value = await redis_client.delete(PIPLEINE_LOCK_KEY)

    if value == lock_token:
        await redis_client.delete(PIPLEINE_LOCK_KEY)
