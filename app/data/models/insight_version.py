from dataclasses import dataclass
from datetime import datetime
from typing import List


# This models for stored versions.
@dataclass
class InsightVersion:
    id: str
    insight_id: str
    version: int
    summary: str
    confidence: float
    sources: List[str]
    created_at: datetime
