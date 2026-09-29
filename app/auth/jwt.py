from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from app.config.settings import settings


ALGORITHM = "HS256"


def create_access_token(
    data: dict, expires_delta: timedelta = timedelta(hours=2)
) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})

    secret_key = settings.jwt_secret_key.get_secret_value()

    return jwt.encode(to_encode, secret_key, algorithm=ALGORITHM)


def verify_token(token: str) -> dict:
    try:
        secret_key = settings.jwt_secret_key.get_secret_value()
        return jwt.decode(token, secret_key, algorithms=[ALGORITHM])
    except JWTError as e:
        # TODO: Log and re-raise, or return a custom error structure
        raise e
