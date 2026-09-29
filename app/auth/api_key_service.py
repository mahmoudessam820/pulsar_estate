import logging
import hashlib
import secrets
from typing import List

from app.data.models.api_keys import ApiKey
from app.data.repositories.base import ApiKeyRepositoryBase

logger = logging.getLogger(__name__)


class ApiKeyService:
    def __init__(self, api_key_repo: ApiKeyRepositoryBase):
        self.api_key_repo = api_key_repo

    def _generate_raw_key(self) -> str:
        """
        Generate a secure random API key with a prefix.
        The prefix is used for identification and can be customized as needed.
        The rest of the key is generated using a secure random function to ensure high entropy and uniqueness.
        """
        return f"pe_live_{secrets.token_urlsafe(32)}"

    def _hash_key(self, raw_key: str) -> str:
        """
        Hash the raw API key using SHA-256 for secure storage.
        """
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

    async def create_api_key(self, user_id: str, name: str) -> dict:
        raw_key = self._generate_raw_key()
        prefix = raw_key[:10]  # e.g., "pe_live_a1"
        hashed_key = self._hash_key(raw_key)

        new_key = await self.api_key_repo.create(
            user_id=user_id, name=name, hashed_key=hashed_key, prefix=prefix
        )

        logger.info(f"Created API key {new_key.id} for user {user_id}")

        # Return the raw key ONLY once. It is never stored in the DB.
        return {
            "id": new_key.id,
            "name": new_key.name,
            "prefix": new_key.prefix,
            "raw_key": raw_key,
        }

    async def list_api_keys(self, user_id: str) -> List[ApiKey]:
        return await self.api_key_repo.get_by_user(user_id)

    async def revoke_api_key(self, user_id: str, key_id: str) -> None:
        # Fetch the key to verify ownership (prevents IDOR attacks)
        key = await self.api_key_repo.get_by_id(key_id)

        if not key:
            raise ValueError("API key not found")

        # Strict ownership check
        if str(key.user_id) != user_id:
            raise PermissionError("You do not have permission to revoke this key")

        await self.api_key_repo.revoke(key_id)
        logger.info(f"Revoked API key {key_id} for user {user_id}")
