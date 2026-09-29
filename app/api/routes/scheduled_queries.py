import uuid
import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import get_current_user
from app.core.scheduler.scheduled_query_service import ScheduledQueryService
from app.api.deps import get_scheduled_query_service, get_entitlement_service
from app.api.schemas.scheduled_queries import (
    ScheduledQueryCreateRequest,
    ScheduledQueryResponse,
    ScheduledQueryToggleRequest,
)
from app.data.models.users import User
from app.monetization.entitlements import EntitlementService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/scheduled-queries", tags=["Scheduled Queries"])


@router.post(
    "",
    response_model=ScheduledQueryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a scheduled query",
    description="Save a query to run daily at a specific time. Subject to plan limits.",
)
async def create_scheduled_query(
    request: ScheduledQueryCreateRequest,
    current_user: User = Depends(get_current_user),
    service: ScheduledQueryService = Depends(get_scheduled_query_service),
    entitlement_service: EntitlementService = Depends(get_entitlement_service),
):
    # Check quota
    can_create = await entitlement_service.check_scheduled_query_access(current_user)
    if not can_create:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Scheduled query limit reached for your plan. Please upgrade.",
        )

    try:
        new_query = await service.create_scheduled_query(
            user_id=str(current_user.id),
            query_text=request.query_text,
            execution_time_str=request.execution_time,
            timezone=request.timezone,
        )
        return new_query
    except Exception as e:
        logger.error(
            f"Failed to create scheduled query for user {current_user.id}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create scheduled query",
        )


@router.get(
    "",
    response_model=list[ScheduledQueryResponse],
    summary="List scheduled queries",
    description="Retrieve all scheduled queries for the current user.",
)
async def list_scheduled_queries(
    current_user: User = Depends(get_current_user),
    service: ScheduledQueryService = Depends(get_scheduled_query_service),
):
    queries = await service.list_scheduled_queries(str(current_user.id))
    return queries


@router.patch(
    "/{query_id}/toggle",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Toggle a scheduled query",
    description="Activate or pause a scheduled query.",
)
async def toggle_scheduled_query(
    query_id: uuid.UUID,
    request: ScheduledQueryToggleRequest,
    current_user: User = Depends(get_current_user),
    service: ScheduledQueryService = Depends(get_scheduled_query_service),
):
    try:
        await service.toggle_scheduled_query(
            user_id=str(current_user.id),
            query_id=str(query_id),
            is_active=request.is_active,
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Scheduled query not found"
        )
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to modify this query",
        )
    except Exception as e:
        logger.error(f"Failed to toggle scheduled query {query_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to toggle scheduled query",
        )


@router.delete(
    "/{query_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a scheduled query",
    description="Permanently delete a scheduled query.",
)
async def delete_scheduled_query(
    query_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: ScheduledQueryService = Depends(get_scheduled_query_service),
):
    try:
        await service.delete_scheduled_query(
            user_id=str(current_user.id), query_id=str(query_id)
        )
        logger.info(f"Deleted scheduled query {query_id} for user {current_user.id}")
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Scheduled query not found"
        )
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this query",
        )
    except Exception as e:
        logger.error(f"Failed to delete scheduled query {query_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete scheduled query",
        )
