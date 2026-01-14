from abc import ABC, abstractmethod
from typing import Dict


class CrawlProviderBase(ABC):
    @abstractmethod
    async def crawl(self, url: str) -> Dict:
        """Crawl the given URL and return the extracted data as a dictionary."""
        raise NotImplementedError
