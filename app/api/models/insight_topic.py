from typing import Optional, List, Dict

from pydantic import BaseModel


class InsightTopic(BaseModel):
    id: str
    topic: str
    created_at: str


class ConfidenceModel(BaseModel):
    score: float
    label: str
    badge: str
    source_strength: float
    evidence_coverage: float
    freshness: float
    consensus: float
    sources_count: int


class InsightVersion(BaseModel):
    id: str
    topic_id: str
    version: int
    summary: str
    confidence: Optional[ConfidenceModel] = None
    sources: List[str]
    created_at: str


class InsightTopicResponse(BaseModel):
    version: Dict  # Or use InsightVersion if you prefer typed
    topics: List[InsightTopic]
