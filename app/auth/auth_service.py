import uuid
from datetime import datetime

from passlib.context import CryptContext

from app.auth.models import User


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    def __init__(self):
        # TEMPLATE: In-memory user store, replace with database latter
        self.users = {}

    def hash_password(self, password: str) -> str:
        return pwd_context.hash(password)

    def verify_password(self, plain: str, hashed: str) -> bool:
        return pwd_context.verify(plain, hashed)

    async def register(self, email: str, password: str) -> User:
        user = User(
            id=uuid.uuid4().int,
            email=email,
            password_hash=self.hash_password(password),
            created_at=datetime.utcnow(),
        )

        self.users[email] = user

        return user

    async def authenticate(self, email: str, password: str) -> User | None:
        user = self.users.get(email)

        if not user:
            return None

        if not self.verify_password(password, user.password_hash):
            return None

        return user
