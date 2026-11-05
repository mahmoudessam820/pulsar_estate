from fastapi import APIRouter

from app.core.limiter import limiter

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/")
@limiter.exempt  # Exempt the health check endpoint from rate limiting
async def check_health():
    """
    Health check endpoint to verify the service is running.
    """
    return {"status": "ok"}
