from datetime import datetime

from app.data.repositories.user_repo import JSONUserRepository


async def handle_subscription_expired(user_id: str):
    user_repo = JSONUserRepository()

    await user_repo.update_subscription(
        user_id=user_id,
        subscription_data={
            "plan": "free",
            "subscription_status": "expired",
            "updated_at": datetime.now().isoformat(),
        },
    )
