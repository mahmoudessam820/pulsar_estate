from fastapi import APIRouter, Depends, HTTPException

from app.data.repositories.base import InsightsHistoryRepositoryBase
from app.api.deps import get_insights_history_repository
from app.api.models.insights_history import InsightsHistory
from app.api.models.insights_history import InsightsHistoryResponse


router = APIRouter(prefix="/insights", tags=["Insights-History"])


@router.get("/history", response_model=InsightsHistory)
async def get_pipeline_history(
    repo: InsightsHistoryRepositoryBase = Depends(get_insights_history_repository),
):
    insight_history: list[InsightsHistoryResponse] = await repo.load_history(limit=10)

    if not insight_history:
        raise HTTPException(status_code=404, detail="No insight history found")
    return InsightsHistory(insights_history_list=insight_history)
