from dataclasses import dataclass
from datetime import datetime
from typing import Optional


# This model for records every pipeline run execution.
@dataclass
class InsightsHistory:
    id: str
    query: str
    timestamp: datetime
    summary: Optional[str] = None
    confidence_score: Optional[float] = None
    duration_seconds: Optional[float] = None
    error: Optional[str] = None
