import logging
from typing import Dict

from rich.console import Console
from crawl4ai import AsyncWebCrawler

from app.providers.crawler.base import CrawlProviderBase


logger = logging.getLogger(__name__)
console = Console()


class Crawl4AIProvider(CrawlProviderBase):
    def __init__(self, timeout: int = 20):
        self.timeout = timeout
        self._crawler = None

    async def _get_crawler(self) -> AsyncWebCrawler:
        if self._crawler is None:
            logger.info("Initializing Crawl4AI crawler (timeout=%d)", self.timeout)
            console.print(
                f"[dim]Starting Crawl4AI crawler (timeout {self.timeout}s)[/dim]"
            )

            self._crawler = AsyncWebCrawler(timeout=self.timeout)
            await self._crawler.start()

            console.print("[green]Crawl4AI crawler ready[/green]")

        return self._crawler

    async def crawl(self, url: str) -> Dict:
        logger.info("Crawling URL: %s", url)
        console.print(f"[cyan]→ Crawling[/cyan] {url}")

        try:
            crawler = await self._get_crawler()
            result = await crawler.arun(url=url)

            if not result or not result.markdown:
                logger.warning("Empty or invalid crawl result for %s", url)
                console.print("[yellow]Warning: empty content returned[/yellow]")
                return {
                    "url": url,
                    "title": None,
                    "content": None,
                    "published_at": None,
                    "author": None,
                    "error": "Empty content",
                }

            logger.info(
                "Successfully crawled %s | markdown length: %d",
                url,
                len(result.markdown or ""),
            )
            console.print(
                f"[green]✓ Crawled successfully[/green] ({len(result.markdown or ''):,} chars)"
            )

            return {
                "url": url,
                "title": result.metadata.get("title"),
                "content": result.markdown,
                "published_at": result.metadata.get("published_date"),
                "author": result.metadata.get("author"),
                "error": None,
            }

        except Exception as exc:
            logger.error("Crawl failed for %s : %s", url, exc, exc_info=True)
            console.print(f"[red]Error during crawl:[/red] {str(exc)}")
            return {
                "url": url,
                "title": None,
                "content": None,
                "published_at": None,
                "author": None,
                "error": str(exc),
            }

    async def close(self) -> None:
        if self._crawler:
            logger.info("Closing Crawl4AI crawler")
            console.print("[dim]Closing crawler...[/dim]")

            await self._crawler.close()
            self._crawler = None

            console.print("[dim]Crawler closed[/dim]")
