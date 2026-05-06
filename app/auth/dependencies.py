from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.auth.jwt import verify_token
from app.api.deps import get_user_repository


security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    user_repo=Depends(get_user_repository),
):
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
