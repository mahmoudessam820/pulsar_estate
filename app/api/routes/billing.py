from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import get_current_user
from app.api.deps import get_user_repository
from app.api.schemas.billing import SubscribeRequest, SubscribeResponse, CancelResponse
from app.billing.subscriptions import SubscriptionService


router = APIRouter(prefix="/billing", tags=["Billing"])


@router.post(
    "/subscribe",
    response_model=SubscribeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Subscribe to a billing plan",
)
async def subscribe(
    request: SubscribeRequest,
    current_user=Depends(get_current_user),
    user_repo=Depends(get_user_repository),
):
    service = SubscriptionService(user_repo)

    if current_user.subscription_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already has an active subscription",
        )

    subscription = await service.subscribe_user(
        user_id=current_user.id, plan=request.plan
    )

    return SubscribeResponse(
        message=f"User {current_user.email} subscribed to {request.plan} plan",
        subscription=subscription,
    )


@router.post(
    "/cancel",
    response_model=CancelResponse,
    status_code=status.HTTP_200_OK,
    summary="Cancel the current subscription",
)
async def cancel_subscription(
    current_user=Depends(get_current_user),
    user_repo=Depends(get_user_repository),
):
    if not current_user.subscription_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not have an active subscription",
        )

    service = SubscriptionService(user_repo)

    await service.cancel_subscription(
        user_id=current_user.id, subscription_id=current_user.subscription_id
    )

    return CancelResponse(
        message=f"Subscription for user {current_user.email} has been cancelled."
    )
