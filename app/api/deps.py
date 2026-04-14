from app.data.repositories.base import (
    InsightRepositoryBase,
    InsightsHistoryRepositoryBase,
)
from app.data.repositories.insight_repo import JSONInsightRepository
from app.data.repositories.insights_history_repo import InsightsHistoryRepository


def get_insight_repository() -> InsightRepositoryBase:
    return JSONInsightRepository()


def get_insights_history_repository() -> InsightsHistoryRepositoryBase:
    return InsightsHistoryRepository()
