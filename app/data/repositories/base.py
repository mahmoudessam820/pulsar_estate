from abc import ABC, abstractmethod
from typing import Dict, Optional


class InsightRepositoryBase(ABC):
    @abstractmethod
    async def save(self, data: Dict) -> None:
        """Save insight data to the repository."""
        raise NotImplementedError

    @abstractmethod
    async def load_latest(self) -> Optional[Dict]:
        """Load the latest insight data from the repository."""
        raise NotImplementedError
