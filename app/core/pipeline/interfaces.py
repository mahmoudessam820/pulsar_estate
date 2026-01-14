from abc import ABC, abstractmethod
from typing import List, Dict


class SearchProvider(ABC):
    @abstractmethod
    async def search(self, query: str) -> List[str]:
        """Return a list of URLs"""
        raise NotImplementedError


class CrawlProvider(ABC):
    @abstractmethod
    async def crawl(self, url: str) -> Dict:
        """Return extracted content + metadata"""
        raise NotImplementedError


class AIProvider(ABC):
    @abstractmethod
    async def analyze(self, documents: List[Dict]) -> Dict:
        """Return structured insights"""
        raise NotImplementedError
