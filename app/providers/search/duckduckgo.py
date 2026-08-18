import logging
from typing import List

from ddgs import DDGS
from rich.console import Console

from app.providers.search.base import SearchProviderBase
from app.providers.search.utils import (
    normalize_query,
    has_meaningful_content,
    filter_blacklisted_urls,
)


logger = logging.getLogger(__name__)
console = Console()


class DuckDuckGoSearchProvider(SearchProviderBase):
    def __init__(self, max_results: int = 25):
        self.max_results = max_results

    async def search(self, query: str) -> List[str]:
        normalized_query = normalize_query(query)

        console.print(f"[dim]→ DDG search:[/] {query}", style="cyan")

        urls: List[str] = []

        with DDGS() as ddgs:
            results = ddgs.text(
                normalized_query,
                max_results=self.max_results,
            )

            for r in results:
                url = r.get("href")
                if url and has_meaningful_content(url):
                    urls.append(url)

        # Filter out blacklisted URLs
        filtered_urls = filter_blacklisted_urls(urls)

        # Log how many were removed for transparency
        filtered_count = len(urls) - len(filtered_urls)
        if filtered_count > 0:
            logger.info("Filtered out %d blacklisted URL(s)", filtered_count)

        logger.info("DuckDuckGo search finished - found %d urls", len(urls))
        console.print(
            f"[green]✓ Found {len(urls)} link{'s' if len(urls) != 1 else ''}[/]"
        )

        return filtered_urls
