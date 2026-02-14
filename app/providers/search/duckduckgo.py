import logging
from typing import List

from ddgs import DDGS
from rich.console import Console

from app.providers.search.base import SearchProviderBase
from app.providers.search.utils import normalize_query


logger = logging.getLogger(__name__)
console = Console()


class DuckDuckGoSearchProvider(SearchProviderBase):
    def __init__(self, max_results: int = 15):
        self.max_results = max_results

    async def search(self, query: str) -> List[str]:
        normalized_query = normalize_query(query)

        console.print(f"[dim]→ DDG search:[/] {query}", style="cyan")

        urls: List[str] = []

        with DDGS() as ddgs:
            results = ddgs.text(
                normalized_query,
                max_results=self.max_results,
                # region="en-ae",
            )

            for r in results:
                url = r.get("href")
                if url:
                    urls.append(url)

        logger.info("DuckDuckGo search finished - found %d urls", len(urls))
        console.print(
            f"[green]✓ Found {len(urls)} link{'s' if len(urls) != 1 else ''}[/]"
        )

        return urls
