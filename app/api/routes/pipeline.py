from fastapi import Depends, HTTPException, APIRouter

from app.auth.dependencies import get_current_user
from app.api.deps import get_entitlement_service
from app.monetization.entitlements import EntitlementService
from app.core.pipeline.factory import build_pipeline


router = APIRouter(prefix="/pipeline-query", tags=["Pipeline"])


@router.post("/run")
async def run_pipeline(
    query: str,
    user=Depends(get_current_user),
    entitlement: EntitlementService = Depends(get_entitlement_service),
):
    # Check if user has access to run the pipeline
    if not await entitlement.check_pipeline_access(user):
        raise HTTPException(
            status_code=403, detail="Pipeline run limit exceeded for today"
        )

    # Build and execute the pipeline
    pipeline = build_pipeline()
    result = await pipeline.run(query)

    # Record the pipeline run for usage tracking
    await entitlement.record_pipeline_run(user)

    return result
