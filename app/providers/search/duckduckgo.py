from typing import List
from ddgs import DDGS

from app.providers.search.base import SearchProviderBase
from app.providers.search.utils import normalize_query


class DuckDuckGoSearchProvider(SearchProviderBase):
    def __init__(self, max_results: int = 10):
        self.max_results = max_results

    def search(self, query: str) -> List[str]:
        normalized_query = normalize_query(query)

        urls: List[str] = []

        with DDGS() as ddgs:
            results = ddgs.text(
                normalized_query,
                max_results=self.max_results,
            )

            for r in results:
                url = r.get("href")
                if url:
                    urls.append(url)

        return urls
