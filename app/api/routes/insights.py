from fastapi import APIRouter, Depends, HTTPException


from app.data.repositories.base import InsightRepositoryBase
from app.api.deps import get_insight_repository
from app.api.models.insight import InsightResponse


router = APIRouter(prefix="/insights", tags=["Insights"])


@router.get("/latest", response_model=InsightResponse)
async def get_latest_insight(
    repo: InsightRepositoryBase = Depends(get_insight_repository),
):
    insight = await repo.load_latest()

    if not insight:
        raise HTTPException(status_code=404, detail="No insights found")

    return insight
