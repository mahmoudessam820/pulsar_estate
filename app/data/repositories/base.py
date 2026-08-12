from abc import ABC, abstractmethod
from typing import Dict, Optional, List

from app.data.models.insights import Insights
from app.data.models.insight_topic import InsightTopic
from app.data.models.insight_version import InsightVersion
from app.data.models.insights_history import InsightsHistory
from app.auth.models import User


class InsightRepositoryBase(ABC):
    @abstractmethod
    async def save(self, data: Dict[str, str]) -> None:
        """Save insight data to the repository."""
        raise NotImplementedError

    @abstractmethod
    async def load_latest(self) -> Optional[Insights]:
        """Load the latest insight data from the repository."""
        raise NotImplementedError

    @abstractmethod
    async def create_insight_topic(self, topic: Dict[str, str]) -> InsightTopic:
        """Create a new insight topic record."""
        raise NotImplementedError

    @abstractmethod
    async def add_version(self, version: InsightVersion) -> None:
        """Add a new version to an existing insight."""
        raise NotImplementedError

    @abstractmethod
    async def get_latest_version(self, insight_id: str) -> InsightVersion:
        """Get the latest version of an insight."""
        raise NotImplementedError

    @abstractmethod
    async def load_topics(self, topic_id: str) -> List[InsightVersion]:
        """List all versions of an insight."""
        raise NotImplementedError


class InsightsHistoryRepositoryBase(ABC):
    @abstractmethod
    async def save_history(self, data: InsightsHistory) -> None:
        raise NotImplementedError

    @abstractmethod
    async def load_history(self, limit: int) -> List[InsightsHistory]:
        raise NotImplementedError


class UserRepositoryBase(ABC):
    @abstractmethod
    async def create(self, user: User) -> None:
        raise NotImplementedError

    @abstractmethod
    async def list_users(self) -> List[User]:
        raise NotImplementedError

    @abstractmethod
    async def update_user(self, user_id: str, user_data: dict) -> None:
        raise NotImplementedError

    @abstractmethod
    async def update_role(self, user_id: str, role: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def update_plan(self, user_id: str, plan: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, user_id: str) -> Optional[User]:
        raise NotImplementedError

    @abstractmethod
    async def update_subscription(self, user_id: str, subscription_data: Dict) -> None:
        raise NotImplementedError


class UsageRepositoryBase(ABC):
    @abstractmethod
    async def count_today(self, user_id: str) -> int:
        raise NotImplementedError

    @abstractmethod
    async def increment(self, user_id: str) -> None:
        raise NotImplementedError
