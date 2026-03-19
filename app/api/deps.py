from app.data.repositories.base import InsightRepositoryBase
from app.data.repositories.insight_repo import JSONInsightRepository


def get_insight_repository() -> InsightRepositoryBase:
    return JSONInsightRepository()
