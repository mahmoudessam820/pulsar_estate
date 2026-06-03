import json
import logging
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

    async def list_users(self) -> list[User]:
        data = self._load()
        return list(data.values())

    async def update_user(self, user_id: str, user_data: dict) -> None:
        data = self._load()

        if user_id not in data:
            return

        user = data[user_id]

        user["email"] = user_data.get("email", user["email"])
        user["password_hash"] = user_data.get("password_hash", user["password_hash"])
        user["role"] = user_data.get("role", user["role"])
        user["plan"] = user_data.get("plan", user["plan"])
        user["is_active"] = user_data.get("is_active", user["is_active"])
        user["subscription_id"] = user_data.get(
            "subscription_id", user["subscription_id"]
        )
        user["subscription_status"] = user_data.get(
            "subscription_status", user["subscription_status"]
        )
        user["current_period_end"] = user_data.get(
            "current_period_end", user["current_period_end"]
        )
        user["updated_at"] = user_data.get("updated_at", user.get("updated_at"))

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

    async def update_subscription(self, user_id: str, subscription_data: dict) -> None:
        logging.info(
            f"Updating subscription for user_id={user_id} with data={subscription_data}"
        )
        await self.update_user(user_id, subscription_data)
