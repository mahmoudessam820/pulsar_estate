from fastapi import APIRouter, Depends, HTTPException, Header

from app.core.pipeline.factory import build_pipeline
from app.config.settings import settings


router = APIRouter(prefix="/pipeline", tags=["Pipeline"])


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
