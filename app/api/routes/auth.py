from fastapi import APIRouter, HTTPException, Depends

from app.auth.jwt import create_access_token
from app.api.deps import get_auth_service
from app.auth.auth_service import AuthService


router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register")
async def register(
    email: str,
    password: str,
    auth_service: AuthService = Depends(get_auth_service),
):
    user = await auth_service.register(email, password)
    return {"id": user.id, "email": user.email}


@router.post("/login")
async def login(
    email: str,
    password: str,
    auth_service: AuthService = Depends(get_auth_service),
):
    user = await auth_service.authenticate(email, password)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": user.id})

    return {"access_token": token}
