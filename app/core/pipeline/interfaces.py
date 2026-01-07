from abc import ABC, abstractmethod
from typing import List, Dict


class SearchProvider(ABC):
    @abstractmethod
    def search(self, query: str) -> List[str]:
        """Return a list of URLs"""
        pass


class CrawlProvider(ABC):
    @abstractmethod
    def crawl(self, url: str) -> Dict:
        """Return extracted content + metadata"""
        pass


class AIProvider(ABC):
    @abstractmethod
    def analyze(self, documents: List[Dict]) -> Dict:
        """Return structured insights"""
        pass
