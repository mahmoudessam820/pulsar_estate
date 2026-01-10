import asyncio
from typing import Dict

from crawl4ai import AsyncWebCrawler

from app.providers.crawler.base import CrawlProviderBase


class Crawl4AIProvider(CrawlProviderBase):
    def __init__(self, timeout: int = 20):
        self.timeout = timeout

    async def _crawl_async(self, url: str) -> Dict:
        async with AsyncWebCrawler(timeout=self.timeout) as crawler:
            result = await crawler.arun(url=url)

            return {
                "url": url,
                "title": result.metadata.get("title"),
                "content": result.markdown,
                "published_at": result.metadata.get("published_date"),
                "author": result.metadata.get("author"),
                "error": None,
            }

    def crawl(self, url: str) -> Dict:
        """
        Sync wrapper to allow usage inside sync pipelines and schedulers.
        """
        try:
            return asyncio.run(self._crawl_async(url))
        except Exception as exc:
            return {
                "url": url,
                "title": None,
                "content": None,
                "published_at": None,
                "author": None,
                "error": str(exc),
            }
