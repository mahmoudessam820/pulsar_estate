from typing import Dict

from crawl4ai import AsyncWebCrawler

from app.providers.crawler.base import CrawlProviderBase


class Crawl4AIProvider(CrawlProviderBase):
    def __init__(self, timeout: int = 20):
        self.timeout = timeout
        self._crawler = None

    async def _get_crawler(self) -> AsyncWebCrawler:
        if self._crawler is None:
            self._crawler = AsyncWebCrawler(timeout=self.timeout)
            await self._crawler.start()
        return self._crawler

    async def crawl(self, url: str) -> Dict:
        try:
            crawler = await self._get_crawler()
            result = await crawler.arun(url=url)

            if not result or not result.markdown:
                return {
                    "url": url,
                    "title": None,
                    "content": None,
                    "published_at": None,
                    "author": None,
                    "error": "Empty content",
                }

            return {
                "url": url,
                "title": result.metadata.get("title"),
                "content": result.markdown,
                "published_at": result.metadata.get("published_date"),
                "author": result.metadata.get("author"),
                "error": None,
            }

        except Exception as exc:
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
            await self._crawler.close()
            self._crawler = None
