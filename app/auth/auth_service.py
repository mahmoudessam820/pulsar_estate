import uuid
from datetime import datetime, timezone

from passlib.context import CryptContext

from app.auth.models import User
from app.data.repositories.base import UserRepositoryBase

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


class AuthService:
    def __init__(self, user_repo: UserRepositoryBase):
        self.user_repo = user_repo

    def _hash_password(self, password: str) -> str:
        return pwd_context.hash(password)

    def _verify_password(self, plain: str, hashed: str) -> bool:
        return pwd_context.verify(plain, hashed)

    async def register(self, email: str, password: str) -> User:
        existing = await self.user_repo.get_by_email(email)

        if existing:
            raise ValueError("Email already registered")

        user = User(
            id=str(uuid.uuid4()),
            email=email,
            password_hash=self._hash_password(password),
            created_at=datetime.now(timezone.utc).strftime("%Y, %-m, %-d"),
        )

        await self.user_repo.create(user)

        return user

    async def authenticate(self, email: str, password: str) -> User | None:
        user = await self.user_repo.get_by_email(email)

        if not user:
            return None

        if not self._verify_password(password, user.password_hash):
            return None

        return user
