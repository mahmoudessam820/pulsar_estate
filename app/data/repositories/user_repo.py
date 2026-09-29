import uuid
import logging
from typing import Dict, Optional, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.data.repositories.base import UserRepositoryBase
from app.data.models.users import User

logger = logging.getLogger(__name__)


class PostgresUserRepository(UserRepositoryBase):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, user: User) -> None:
        try:
            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)
            logger.info(f"Successfully created user {user.id} with email {user.email}")
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to create user {user.email}: {str(e)}", exc_info=True)
            raise

    async def list_users(self) -> List[User]:
        try:
            result = await self.db.execute(
                select(User).order_by(User.created_at.desc())
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to list users: {str(e)}", exc_info=True)
            raise

    async def update_user(self, user_id: str, user_data: dict) -> None:
        try:
            stmt = select(User).where(User.id == uuid.UUID(user_id))
            result = await self.db.execute(stmt)
            user = result.scalar_one_or_none()

            if not user:
                logger.warning(f"Attempted to update non-existent user: {user_id}")
                return

            for key, value in user_data.items():
                if hasattr(user, key):
                    setattr(user, key, value)

            await self.db.commit()
            await self.db.refresh(user)
            logger.info(f"Successfully updated user {user_id}")
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to update user {user_id}: {str(e)}", exc_info=True)
            raise

    async def update_role(self, user_id: str, role: str) -> None:
        await self.update_user(user_id, {"role": role})

    async def update_plan(self, user_id: str, plan: str) -> None:
        await self.update_user(user_id, {"plan": plan})

    async def get_by_email(self, email: str) -> Optional[User]:
        try:
            result = await self.db.execute(select(User).where(User.email == email))
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(
                f"Failed to get user by email {email}: {str(e)}", exc_info=True
            )
            raise

    async def get_by_id(self, user_id: str) -> Optional[User]:
        try:
            result = await self.db.execute(
                select(User).where(User.id == uuid.UUID(user_id))
            )
            return result.scalar_one_or_none()
        except ValueError:
            logger.warning(f"Invalid UUID format for user_id: {user_id}")
            return None
        except Exception as e:
            logger.error(f"Failed to get user by id {user_id}: {str(e)}", exc_info=True)
            raise

    async def update_subscription(self, user_id: str, subscription_data: Dict) -> None:
        await self.update_user(user_id, subscription_data)
