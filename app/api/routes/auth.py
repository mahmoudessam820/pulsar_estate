import logging

from fastapi import APIRouter, HTTPException, Depends, status

from app.auth.jwt import create_access_token
from app.api.deps import get_auth_service
from app.api.schemas import RegisterRequest, loginRequest, AuthResponse, UserPublic
from app.auth.auth_service import AuthService


router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED
)
async def register(
    request: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    try:
        user = await auth_service.register(request.email, request.password)
        logging.info(f"User registered: {request.email}")
        return user
    except Exception as e:
        logging.error(f"Registration failed for {request.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Registration failed"
        )


@router.post("/login", response_model=AuthResponse)
async def login(
    request: loginRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    user = await auth_service.authenticate(request.email, request.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    token = create_access_token(data={"sub": user.id})
    logging.info(f"User logged in: {request.email}")

    return AuthResponse(access_token=token, user=user)
