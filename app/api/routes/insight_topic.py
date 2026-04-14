from fastapi import APIRouter, Depends, HTTPException

from app.data.repositories.base import InsightRepositoryBase
from app.api.deps import get_insight_repository
from app.api.models.insight_topic import InsightTopicResponse


router = APIRouter(prefix="/insight-topics", tags=["Insight Topics"])


@router.get("/latest/{topic_id}", response_model=InsightTopicResponse)
async def get_insight_topics(
    topic_id: str, repo: InsightRepositoryBase = Depends(get_insight_repository)
):
    version = await repo.get_latest_version(topic_id)

    topics = await repo.load_topics(version["topic_id"])

    if not topics:
        raise HTTPException(status_code=404, detail="No insight topics found")

    return {"version": version, "topics": topics}
