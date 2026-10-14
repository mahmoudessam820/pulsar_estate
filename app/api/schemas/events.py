from typing import Optional

from pydantic import BaseModel


class TaskCompletionEvent(BaseModel):
    task_id: str
    status: str  # "success" or "failed"
    insight_id: Optional[str] = None
    error: Optional[str] = None
