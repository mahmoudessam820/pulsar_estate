from abc import ABC, abstractmethod
from typing import Dict, Optional, List

from app.data.models.insight_topic import InsightTopic
from app.data.models.insight_version import InsightVersion
from app.data.models.insights_history import InsightsHistory


class InsightRepositoryBase(ABC):
    @abstractmethod
    async def save(self, data: Dict) -> None:
        """Save insight data to the repository."""
        raise NotImplementedError

    @abstractmethod
    async def load_latest(self) -> Optional[Dict]:
        """Load the latest insight data from the repository."""
        raise NotImplementedError

    @abstractmethod
    async def create_insight_topic(self, topic: str) -> InsightTopic:
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
