from fastapi import APIRouter, Depends, HTTPException, status

from app.data.repositories.base import InsightsHistoryRepositoryBase
from app.api.deps import get_insights_history_repository
from app.api.schemas import InsightsHistory


router = APIRouter(prefix="/insights", tags=["Insights-History"])


@router.get(
    "/history",
    response_model=InsightsHistory,
    response_model_exclude_none=True,
    summary="Get insight generation history",
    description="Returns a list of recent insight generation requests with summaries and metadata.",
)
async def get_pipeline_history(
    repo: InsightsHistoryRepositoryBase = Depends(get_insights_history_repository),
):
    insight_history = await repo.load_history(limit=20)

    if not insight_history:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No insight history found"
        )

    return InsightsHistory(insights_history_list=insight_history)
