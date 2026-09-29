import uuid
import logging
from typing import List, Optional
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func

from app.data.repositories.base import ApiKeyRepositoryBase
from app.data.models.api_keys import ApiKey

logger = logging.getLogger(__name__)


class PostgresApiKeyRepository(ApiKeyRepositoryBase):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self, user_id: str, name: str, hashed_key: str, prefix: str
    ) -> ApiKey:
        """Create a new API key."""
        try:
            user_uuid = uuid.UUID(user_id)

            new_key = ApiKey(
                user_id=user_uuid, name=name, hashed_key=hashed_key, prefix=prefix
            )

            self.db.add(new_key)
            await self.db.commit()
            await self.db.refresh(new_key)
            logger.info(f"Created API key {new_key.id} for user {user_id}")
            return new_key
        except ValueError:
            logger.warning(f"Invalid UUID format for user_id: {user_id}")
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to create API key: {str(e)}", exc_info=True)
            raise

    async def get_by_id(self, api_key_id: str) -> Optional[ApiKey]:
        """Get a specific API key by ID."""
        try:
            stmt = select(ApiKey).where(ApiKey.id == uuid.UUID(api_key_id))
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
        except ValueError:
            logger.warning(f"Invalid UUID format for api_key_id: {api_key_id}")
            return None
        except Exception as e:
            logger.error(f"Failed to get API key {api_key_id}: {str(e)}", exc_info=True)
            raise

    async def get_by_user(self, user_id: str) -> List[ApiKey]:
        """Get all API keys for a user."""
        try:
            stmt = (
                select(ApiKey)
                .where(ApiKey.user_id == uuid.UUID(user_id))
                .order_by(ApiKey.created_at.desc())
            )

            result = await self.db.execute(stmt)
            return result.scalars().all()
        except ValueError:
            logger.warning(f"Invalid UUID format for user_id: {user_id}")
            return []
        except Exception as e:
            logger.error(
                f"Failed to get API keys for user {user_id}: {str(e)}", exc_info=True
            )
            raise

    async def get_by_hashed_key(self, hashed_key: str) -> Optional[ApiKey]:
        """Get an API key by its hashed value (for authentication)."""
        try:
            stmt = select(ApiKey).where(ApiKey.hashed_key == hashed_key)

            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get API key by hash: {str(e)}", exc_info=True)
            raise

    async def revoke(self, api_key_id: str) -> None:
        """Revoke an API key (set is_active = false)."""
        try:
            stmt = (
                update(ApiKey)
                .where(ApiKey.id == uuid.UUID(api_key_id))
                .values(is_active=False)
            )

            await self.db.execute(stmt)
            await self.db.commit()
            logger.info(f"Revoked API key {api_key_id}")
        except ValueError:
            logger.warning(f"Invalid UUID format for api_key_id: {api_key_id}")
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(
                f"Failed to revoke API key {api_key_id}: {str(e)}", exc_info=True
            )
            raise

    async def update_last_used(self, api_key_id: str) -> None:
        """Update the last_used_at timestamp."""
        try:
            stmt = (
                update(ApiKey)
                .where(ApiKey.id == uuid.UUID(api_key_id))
                .values(last_used_at=datetime.now(timezone.utc))
            )

            await self.db.execute(stmt)
            await self.db.commit()
        except ValueError:
            logger.warning(f"Invalid UUID format for api_key_id: {api_key_id}")
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(
                f"Failed to update last_used for API key {api_key_id}: {str(e)}",
                exc_info=True,
            )
            raise

    async def count_active_by_user(self, user_id: str) -> int:
        """Count active API keys for a user (for quota enforcement)."""
        try:
            stmt = select(func.count()).where(
                ApiKey.user_id == uuid.UUID(user_id), ApiKey.is_active == True
            )

            result = await self.db.execute(stmt)
            return result.scalar() or 0
        except ValueError:
            logger.warning(f"Invalid UUID format for user_id: {user_id}")
            return 0
        except Exception as e:
            logger.error(
                f"Failed to count active API keys for user {user_id}: {str(e)}",
                exc_info=True,
            )
            raise
