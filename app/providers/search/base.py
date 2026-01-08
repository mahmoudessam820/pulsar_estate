from abc import ABC, abstractmethod
from typing import List


class SearchProviderBase(ABC):
    @abstractmethod
    def search(self, query: str) -> List[str]:
        """Perform a search with the given query string."""
        raise NotImplementedError
