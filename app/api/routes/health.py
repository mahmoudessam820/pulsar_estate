from fastapi import APIRouter


router = APIRouter(prefix="/health", tags=["health"])


@router.get("/")
async def check_health():
    return {"status": "ok"}
