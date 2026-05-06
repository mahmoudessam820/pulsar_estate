import json
from pathlib import Path
from typing import Optional
from dataclasses import asdict

from app.auth.models import User
from app.data.repositories.base import UserRepositoryBase


class JSONUserRepository(UserRepositoryBase):
    def __init__(self, base_path: str = "storage/auth/users.json"):
        self.base_path = Path(base_path)
        self.base_path.parent.mkdir(parents=True, exist_ok=True)

        if not self.base_path.exists():
            self.base_path.write_text(json.dumps({}))

    def _load(self):
        return json.loads(self.base_path.read_text())

    def _save(self, data):
        self.base_path.write_text(json.dumps(data, indent=2))

    async def create(self, user: User) -> None:
        data = self._load()

        data[user.id] = asdict(user)

        self._save(data)

    async def update_role(self, user_id: str, role: str) -> None:
        data = self._load()

        for uid, user in data.items():
            if uid == user_id:
                user["role"] = role
                break

        self._save(data)

    async def update_plan(self, user_id: str, plan: str) -> None:
        data = self._load()

        for uid, user in data.items():
            if uid == user_id:
                user["plan"] = plan
                break

        self._save(data)

    async def get_by_email(self, email: str) -> Optional[User]:
        data = self._load()

        for user_data in data.values():
            if user_data["email"] == email:
                return User(**user_data)

        return None

    async def get_by_id(self, user_id: str) -> Optional[User]:
        data = self._load()

        user_data = data.get(user_id)
        if not user_data:
            return None

        return User(**user_data)
