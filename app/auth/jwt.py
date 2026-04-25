from typing import Optional
from datetime import datetime, timedelta

from jose import jwt

from app.config.settings import settings


ALGORITHM = "HS256"


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()

    expires = datetime.utcnow() + (expires_delta or timedelta(hours=2))
    to_encode.update({"exp": expires})

    jwt_token = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=ALGORITHM)

    return jwt_token


def verify_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret_key, algorithms=[ALGORITHM])
