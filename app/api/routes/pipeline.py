import logging

from fastapi import Depends, HTTPException, APIRouter, status

from app.auth.dependencies import get_current_user
from app.api.deps import get_entitlement_service
from app.monetization.entitlements import EntitlementService
from app.core.pipeline.factory import build_pipeline
from app.api.schemas import PipelineRunRequest, InsightResponse


router = APIRouter(prefix="/pipeline-query", tags=["Pipeline"])


@router.post(
    "/run",
    response_model=InsightResponse,
    status_code=status.HTTP_200_OK,
    summary="Run insight generation pipeline",
    description="Execute the pipeline to generate market insights for a given query. "
    "Requires sufficient pipeline run entitlements.",
)
async def run_pipeline(
    request: PipelineRunRequest,
    user=Depends(get_current_user),
    entitlement: EntitlementService = Depends(get_entitlement_service),
):
    # Check if user has access to run the pipeline
    if not await entitlement.check_pipeline_access(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Pipeline run limit exceeded for today",
        )

    # Build and execute the pipeline
    pipeline = build_pipeline()

    try:
        result = await pipeline.run(request.query)
    except Exception as e:
        # Log the error
        logging.error(f"Pipeline execution failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Pipeline execution failed",
        )
    finally:
        await pipeline.close()

    # Record the pipeline run for usage tracking
    await entitlement.record_pipeline_run(user)

    return result
