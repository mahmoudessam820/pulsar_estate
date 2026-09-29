import uuid
import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import get_current_user, get_current_integration_user
from app.auth.api_key_service import ApiKeyService
from app.api.deps import get_api_key_service
from app.api.schemas.api_keys import (
    ApiKeyCreateRequest,
    ApiKeyCreateResponse,
    ApiKeyResponse,
)
from app.data.models.users import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/integrations", tags=["Integrations"])


@router.post(
    "/api-keys",
    response_model=ApiKeyCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a new API key",
    description="Creates a new API key for third-party integrations. The raw key is returned only once.",
)
async def create_api_key(
    request: ApiKeyCreateRequest,
    current_user: User = Depends(get_current_user),
    service: ApiKeyService = Depends(get_api_key_service),
):
    try:
        result = await service.create_api_key(
            user_id=str(current_user.id), name=request.name
        )
        return result
    except Exception as e:
        logger.error(
            f"Failed to create API key for user {current_user.id}: {e}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate API key",
        )


@router.get(
    "/api-keys",
    response_model=list[ApiKeyResponse],
    summary="List API keys",
    description="Retrieve all API keys associated with the current user.",
)
async def list_api_keys(
    current_user: User = Depends(get_current_user),
    service: ApiKeyService = Depends(get_api_key_service),
):
    keys = await service.list_api_keys(str(current_user.id))
    return keys


@router.delete(
    "/api-keys/{key_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke an API key",
    description="Revokes (deactivates) an existing API key.",
)
async def revoke_api_key(
    key_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: ApiKeyService = Depends(get_api_key_service),
):
    try:
        await service.revoke_api_key(user_id=str(current_user.id), key_id=str(key_id))
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="API key not found"
        )
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to revoke this key",
        )
    except Exception as e:
        logger.error(
            f"Failed to revoke API key {key_id} for user {current_user.id}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke API key",
        )


@router.get(
    "/status",
    summary="Test API Key Authentication",
    description="A protected endpoint that verifies the provided API key and returns the associated user's public profile.",
)
async def get_integration_status(
    current_user: User = Depends(get_current_integration_user),
):
    """
    Returns the authenticated user's profile to prove the API key is valid.
    """
    logger.info(f"Integration status checked by user {current_user.id} via API key")
    return {
        "status": "authenticated",
        "message": "Your API key is valid and active.",
        "user": {
            "id": str(current_user.id),
            "email": current_user.email,
            "plan": current_user.plan,
            "is_active": current_user.is_active,
        },
    }
