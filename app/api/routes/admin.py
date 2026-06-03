import logging

from fastapi import APIRouter, Depends, HTTPException, Header, status

from app.core.pipeline.factory import build_pipeline
from app.config.settings import settings
from app.auth.dependencies import get_current_user
from app.api.deps import get_user_repository
from app.api.schemas import *


router = APIRouter(prefix="/admin", tags=["Admin"])


def verify_admin_key(x_admin_key: str = Header(...)):
    """Verify admin API key from header"""

    if x_admin_key != settings.admin_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized"
        )


@router.post(
    "/run",
    response_model=PipelineRunResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(verify_admin_key)],
    summary="Execute a data pipeline",
)
async def run_pipeline(
    request: RunPipelineRequest,
):
    pipeline = build_pipeline()
    try:
        await pipeline.run(request.query)
        return PipelineRunResponse(
            message=f"Pipeline execute successfully for query: {request.query}",
            query=request.query,
            status="success",
        )
    except Exception as e:
        logging.error(f"Pipeline execution failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Pipeline execution failed",
        )
    finally:
        await pipeline.close()


@router.post(
    "/upgrade-role",
    response_model=RoleUpdateResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(verify_admin_key)],
    summary="Upgrade user role",
)
async def upgrade_user_role(
    request: UpgradeRoleRequest,
    current_user=Depends(get_current_user),
    user_repo=Depends(get_user_repository),
):
    # Doubled check to ensure the user is an admin
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    # Update user role
    user = await user_repo.get_by_id(request.user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    old_role = user.role
    await user_repo.update_role(request.user_id, request.role)

    return RoleUpdateResponse(
        message=f"User {user.email} upgraded role from {old_role} to {request.role}",
        user_id=request.user_id,
        email=user.email,
        old_role=old_role,
        new_role=request.role,
    )


@router.post(
    "/downgrade-role",
    response_model=DowngradeRoleResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(verify_admin_key)],
    summary="Downgrade user role to regular user",
)
async def downgrade_user_role(
    request: DowngradeRoleRequest,
    current_user=Depends(get_current_user),
    user_repo=Depends(get_user_repository),
):
    # Doubled check to ensure the user is an admin
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    # Update user role
    user = await user_repo.get_by_id(request.user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    old_role = user.role
    await user_repo.update_role(request.user_id, "user")

    return DowngradeRoleResponse(
        message=f"User {user.email} downgraded role from {old_role} to user",
        user_id=request.user_id,
        email=user.email,
        old_role=old_role,
        new_role="user",
    )


@router.post(
    "/upgrade-plan",
    response_model=PlanUpdateResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(verify_admin_key)],
    summary="Upgrade user subscription plan",
)
async def upgrade_user_plan(
    request: UpgradePlanRequest,
    current_user=Depends(get_current_user),
    user_repo=Depends(get_user_repository),
):
    # Doubled check to ensure the user is an admin
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    # Update user plan
    user = await user_repo.get_by_id(request.user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    old_plan = user.plan
    await user_repo.update_plan(request.user_id, request.plan)

    return PlanUpdateResponse(
        message=f"User {user.email} plan upgraded from {old_plan} to {request.plan}",
        user_id=request.user_id,
        email=user.email,
        old_plan=old_plan,
        new_plan=request.plan,
    )


@router.post(
    "/downgrade-plan",
    response_model=DowngradePlanResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(verify_admin_key)],
    summary="Downgrade user to free plan",
)
async def downgrade_user_plan(
    request: DowngradePlanRequest,
    current_user=Depends(get_current_user),
    user_repo=Depends(get_user_repository),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    user = await user_repo.get_by_id(request.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    old_plan = user.plan
    await user_repo.update_subscription(
        user_id=request.user_id,
        subscription_data={
            "plan": "free",
            "subscription_status": "manual_downgrade",
        },
    )

    return DowngradePlanResponse(
        message=f"User {user.email} downgraded to free plan",
        user_id=request.user_id,
        email=user.email,
        old_plan=old_plan,
        new_plan="free",
    )
