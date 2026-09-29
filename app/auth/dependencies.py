import logging
import hashlib
from typing import Optional

from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.auth.jwt import verify_token
from app.api.deps import get_user_repository, get_api_key_repository
from app.data.models import User
from app.data.repositories.base import UserRepositoryBase, ApiKeyRepositoryBase


logger = logging.getLogger(__name__)

# Make auto_error=False so it doesn't immediately 403 if the Bearer header is missing
security = HTTPBearer(auto_error=False)


# Dependency to get the current user based on the JWT token
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    user_repo: UserRepositoryBase = Depends(get_user_repository),
):
    """Get the current user based on the JWT token."""
    try:
        payload = verify_token(credentials.credentials)
        user_id = payload["sub"]

        user = await user_repo.get_by_id(user_id)

        if not user:
            raise Exception("User not found")

        return user

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )


# Hashing function for API keys
def _hash_api_key(raw_key: str) -> str:
    """Hashes the raw API key using SHA-256 to match the storage format."""
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


# Dependency to get the current user based on the API key
async def get_current_integration_user(
    x_api_key: str = Header(..., description="Your Pulsar Estate API Key"),
    api_key_repo: ApiKeyRepositoryBase = Depends(get_api_key_repository),
    user_repo: UserRepositoryBase = Depends(get_user_repository),
):
    """
    Authenticates a request using an API key.
    Returns the associated User model if valid and active.
    """
    try:
        hashed_key = _hash_api_key(x_api_key)

        # 1. Lookup the key in the database
        api_key = await api_key_repo.get_by_hashed_key(hashed_key)

        if not api_key:
            logger.warning("Authentication failed: Invalid API key provided")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
            )

        if not api_key.is_active:
            logger.warning(
                f"Authentication failed: Revoked API key used (ID: {api_key.id})"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key has been revoked",
            )

        # 2. Fetch the associated user
        user = await user_repo.get_by_id(str(api_key.user_id))

        if not user or not user.is_active:
            logger.error(
                f"Authentication failed: User associated with API key {api_key.id} not found or inactive"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account associated with this API key is invalid",
            )

        # 3. Audit: Update last_used_at (Fire-and-forget style, non-blocking for response speed)
        # TODO: In a high-throughput scenario, this would be a Celery task.
        await api_key_repo.update_last_used(str(api_key.id))

        logger.info(
            f"Successful API key authentication for user {user.id} (Key ID: {api_key.id})"
        )
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"API key authentication failed with unexpected error: {str(e)}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service error",
        )


# Unified Authentication Dependency (JWT OR API Key)
async def get_authenticated_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    user_repo: UserRepositoryBase = Depends(get_user_repository),
    api_key_repo: ApiKeyRepositoryBase = Depends(get_api_key_repository),
):
    """
    Authenticates a request using either a JWT Bearer token OR an X-API-Key header.
    Returns the associated User model if valid.
    """
    # 1. Try JWT Authentication
    if credentials and credentials.credentials:
        try:
            payload = verify_token(credentials.credentials)
            user = await user_repo.get_by_id(payload["sub"])
            if user and user.is_active:
                return user
        except Exception:
            logger.debug("JWT authentication failed, falling back to API key check")
    # 2. Try API Key Authentication
    if x_api_key:
        try:
            hashed_key = _hash_api_key(x_api_key)
            api_key = await api_key_repo.get_by_hashed_key(hashed_key)

            if api_key and api_key.is_active:
                user = await user_repo.get_by_id(str(api_key.user_id))
                if user and user.is_active:
                    await api_key_repo.update_last_used(str(api_key.id))
                    return user
        except Exception as e:
            logger.error(f"API key authentication error: {e}")

    # 3. If both fail or are missing
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing authentication credentials. Provide a valid Bearer token or X-API-Key.",
    )


# Admin Authentication Dependency
async def get_current_admin_user(
    current_user: User = Depends(get_current_user),
):
    """
    Ensures the authenticated user has admin privileges.
    Raises 403 Forbidden if the user is not an admin.
    """

    if not current_user.role == "admin":
        logger.warning(
            f"Non-admin user {current_user.id} attempted to access admin endpoint"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )

    logger.info(f"Admin access granted for user {current_user.id}")
    return current_user
