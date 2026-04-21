from typing import Optional, List

from pydantic import BaseModel


class InsightsHistoryResponse(BaseModel):
    id: str
    query: str
    summary: Optional[str] = None
    confidence_score: Optional[float] = None
    timestamp: Optional[str] = None
    duration_seconds: Optional[float] = None
    error: Optional[str] = None


class InsightsHistory(BaseModel):
    insights_history_list: List[InsightsHistoryResponse]
