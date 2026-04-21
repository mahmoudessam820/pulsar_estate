from typing import List, Optional

from pydantic import BaseModel


class ConfidenceModel(BaseModel):
    score: float
    label: str
    badge: str
    source_strength: float
    evidence_coverage: float
    freshness: float
    consensus: float
    sources_count: int


class EvidenceItem(BaseModel):
    claim: str
    source_url: str


class InsightContent(BaseModel):
    summary: Optional[str] = None
    key_trends: Optional[List[str]] = None
    market_sentiment: Optional[str] = None
    evidence: Optional[List[EvidenceItem]] = None
    confidence: Optional[ConfidenceModel] = None
    confidence_explanation: Optional[str] = None


class InsightResponse(BaseModel):
    query: str
    documents_collected: int
    sources: List[str]
    insights: InsightContent
