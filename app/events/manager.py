import asyncio
import logging

import redis.asyncio as redis

from app.config.settings import settings

logger = logging.getLogger(__name__)


# Maps each connected user_id to an asyncio.Queue.
# The queue is the bridge between the Redis listener task and the SSE generator that is writing to the HTTP response.
active_connections: dict[str, asyncio.Queue] = {}

# Lazy async redis client for the FastAPI event loop
_redis_client = None


def get_redis_client():
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis(
            host=settings.redis_host, port=settings.redis_port, decode_responses=True
        )
    return _redis_client


async def register_connection(user_id: str) -> asyncio.Queue:
    """Register a new Server-Sent Events (SSE) connection for a user and return the associated queue."""
    queue = asyncio.Queue()
    active_connections[user_id] = queue
    return queue


def unregister_connection(user_id: str):
    """Unregister a user's Server-Sent Events (SSE) connection and clean up resources."""
    if user_id in active_connections:
        del active_connections[user_id]


async def _redis_listener(user_id: str, queue: asyncio.Queue):
    """Background task that listens to Redis Pub/Sub and pushes to the user's queue."""
    client = get_redis_client()
    pubsub = client.pubsub()
    channel = f"task_updates:{user_id}"
    await pubsub.subscribe(channel)

    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                await queue.put(message["data"])
    except asyncio.CancelledError:
        pass  # Expected when client disconnects
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.close()


async def event_generator(user_id: str):
    """Async generator that yields Server-Sent Events (SSE) formatted events to the client."""
    queue = await register_connection(user_id)
    listener_task = asyncio.create_task(_redis_listener(user_id, queue))

    try:
        # Send an initial comment to confirm connection is established
        yield ": connected\n\n"

        while True:
            try:
                # Wait for a message with a timeout to allow checking for disconnects
                data = await asyncio.wait_for(queue.get(), timeout=30.0)
                yield f"data: {data}\n\n"
            except asyncio.TimeoutError:
                # Send a comment ping to keep the connection alive through proxies (e.g., Nginx)
                yield ": ping\n\n"
    finally:
        # Clean up on client disconnect
        listener_task.cancel()
        unregister_connection(user_id)
        logger.info(f"SSE connection closed for user {user_id}")
