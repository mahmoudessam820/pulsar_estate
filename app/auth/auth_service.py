import logging

from passlib.context import CryptContext

from app.data.models.users import User
from app.data.repositories.base import UserRepositoryBase


logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


class AuthService:
    def __init__(self, user_repo: UserRepositoryBase):
        self.user_repo = user_repo

    def _hash_password(self, password: str) -> str:
        return pwd_context.hash(password)

    def _verify_password(self, plain: str, hashed: str) -> bool:
        return pwd_context.verify(plain, hashed)

    async def register(self, email: str, password: str) -> User:
        """Register a new user and return the SQLAlchemy User model."""
        existing = await self.user_repo.get_by_email(email)

        if existing:
            logger.warning(f"Attempted to register already existing email: {email}")
            raise ValueError("Email already registered")

        new_user = User(
            email=email,
            password_hash=self._hash_password(password),
            is_active=True,
            role="user",
            plan="free",
            subscription_status="inactive",
        )

        await self.user_repo.create(new_user)
        logger.info(
            f"Successfully registered new user with email: {email} (ID: {new_user.id})"
        )
        return new_user

    async def authenticate(self, email: str, password: str) -> User | None:
        """Authenticate a user and return the SQLAlchemy User model, or None."""
        user = await self.user_repo.get_by_email(email)

        if not user:
            return None

        if not self._verify_password(password, user.password_hash):
            logger.warning(f"Failed authentication attpempt for email: {email}")
            return None

        return user
