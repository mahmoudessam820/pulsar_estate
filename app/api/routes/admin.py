from fastapi import APIRouter, Depends, HTTPException, Header

from app.core.pipeline.factory import build_pipeline
from app.config.settings import settings
from app.auth.dependencies import get_current_user
from app.api.deps import get_user_repository


router = APIRouter(prefix="/admin", tags=["Admin"])


def verify_admin_key(x_admin_key: str = Header(...)):
    if x_admin_key != settings.admin_api_key:
        raise HTTPException(status_code=401, detail="Unauthorized")


@router.post("/run", dependencies=[Depends(verify_admin_key)])
async def run_pipeline():
    pipeline = build_pipeline()
    try:
        await pipeline.run("Dubai real estate market trends")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await pipeline.close()


@router.post("/upgrade-role", dependencies=[Depends(verify_admin_key)])
async def upgrade_user_role(
    user_id: str,
    role: str,
    current_user=Depends(get_current_user),
    user_repo=Depends(get_user_repository),
):
    # Doubled check to ensure the user is an admin
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Forbidden")

    # Validate role
    if role not in ["user", "developer", "admin"]:
        raise HTTPException(status_code=400, detail="Invalid role")

    # Update user role
    user = await user_repo.get_by_id(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await user_repo.update_role(user_id, role)

    return {"message": f"User {user.email} upgraded to {role} successfully."}


@router.post("/upgrade-plan", dependencies=[Depends(verify_admin_key)])
async def upgrade_user_plan(
    user_id: str,
    plan: str,
    current_user=Depends(get_current_user),
    user_repo=Depends(get_user_repository),
):
    # Doubled check to ensure the user is an admin
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Forbidden")

    # Validate plan
    if plan not in ["free", "pro", "enterprise"]:
        raise HTTPException(status_code=400, detail="Invalid plan")

    # Update user plan
    user = await user_repo.get_by_id(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await user_repo.update_plan(user_id, plan)

    return {"message": f"User {user.email} upgraded to {plan} successfully."}
