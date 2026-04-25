from fastapi import APIRouter, HTTPException

from app.auth.auth_service import AuthService
from app.auth.jwt import create_access_token

router = APIRouter(prefix="/auth", tags=["Auth"])

auth_service = AuthService()


@router.post("/register")
async def register(email: str, password: str):
    user = await auth_service.register(email, password)
    return {"id": user.id, "email": user.email}


@router.post("/login")
async def login(email: str, password: str):
    user = await auth_service.authenticate(email, password)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": user.id})

    return {"access_token": token}
