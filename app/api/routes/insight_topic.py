from fastapi import APIRouter, Depends, HTTPException, Path, status

from app.data.repositories.base import InsightRepositoryBase
from app.api.deps import get_insight_repository
from app.api.schemas import InsightTopicResponse


router = APIRouter(prefix="/insight-topics", tags=["Insight Topics"])


@router.get(
    "/latest/{topic_id}",
    response_model=InsightTopicResponse,
    summary="Get latest version of an insight topic",
    description="Returns the most recent version metadata and associated topics for a given topic ID.",
)
async def get_insight_topics(
    topic_id: str = Path(..., description="The topic UUID to fetch"),
    repo: InsightRepositoryBase = Depends(get_insight_repository),
):
    version = await repo.get_latest_version(topic_id)

    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No version found for topic: {topic_id}",
        )

    topics = await repo.load_topics(version["topic_id"])

    if not topics:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No insight topics found"
        )

    return {"version": version, "topics": topics}
