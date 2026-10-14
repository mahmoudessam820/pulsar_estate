from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.data.models.users import User
from app.auth.dependencies import get_current_user
from app.events.manager import event_generator

router = APIRouter(prefix="/api/v1/events", tags=["Events"])


@router.get(
    "/stream",
    summary="Server-Sent Events stream for task updates",
    description="Connect to this endpoint to receive real-time notifications when your background tasks complete.",
)
async def stream_task_events(current_user: User = Depends(get_current_user)):
    return StreamingResponse(
        event_generator(str(current_user.id)),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Crucial: Disables Nginx buffering of SSE streams
        },
    )
