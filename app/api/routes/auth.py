import logging

from fastapi import APIRouter, HTTPException, Depends, status

from app.auth.jwt import create_access_token
from app.api.deps import get_auth_service
from app.auth.dependencies import get_current_user
from app.data.models import User
from app.api.schemas import RegisterRequest, LoginRequest, AuthResponse, UserPublic
from app.auth.auth_service import AuthService


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])


@router.post(
    "/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED
)
async def register(
    request: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Register a new user with the provided email and password."""
    try:
        user = await auth_service.register(request.email, request.password)
        logger.info(f"User registered: {request.email}")
        return user
    except Exception as e:
        logger.error(f"Registration failed for {request.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Registration failed"
        )


@router.post("/login", response_model=AuthResponse, status_code=status.HTTP_200_OK)
async def login(
    request: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Authenticate a user and return a JWT token along with the user's public profile."""
    user = await auth_service.authenticate(request.email, request.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    token = create_access_token(data={"sub": str(user.id)})
    logger.info(f"User logged in: {request.email}")

    return AuthResponse(access_token=token, user=user)


@router.get(
    "/me",
    response_model=UserPublic,
    status_code=status.HTTP_200_OK,
    summary="Get current user profile",
    description="Validate the current JWT and return the authenticated user's public profile.",
)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
):
    """
    Returns the current authenticated user's profile.
    Pydantic will automatically serialize the SQLAlchemy User model
    into the UserPublic schema using `from_attributes=True`.
    """
    logger.info(f"User profile requested for user_id: {current_user.id}")
    return current_user
