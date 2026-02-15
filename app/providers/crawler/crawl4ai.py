import logging
from typing import Dict
from urllib.parse import urlparse

from rich.console import Console
from crawl4ai import AsyncWebCrawler, UndetectedAdapter
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
from crawl4ai.deep_crawling import DFSDeepCrawlStrategy
from crawl4ai.async_crawler_strategy import AsyncPlaywrightCrawlerStrategy
from crawl4ai.content_scraping_strategy import LXMLWebScrapingStrategy
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.processors.pdf import PDFContentScrapingStrategy, PDFCrawlerStrategy
from crawl4ai.deep_crawling.filters import (
    FilterChain,
    ContentTypeFilter,
    DomainFilter,
)

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

            # Define browser configuration

            # Create browser config with stealth enabled
            self._browser_config = BrowserConfig(
                enable_stealth=True,
                headless=True,
            )

            # Create undetected adapter
            self._adapter = UndetectedAdapter()

            # Create strategy with both features
            self._strategy = AsyncPlaywrightCrawlerStrategy(
                browser_config=self._browser_config, browser_adapter=self._adapter
            )

            # Define crawler configuration

            # Define crawler filters
            self._filter_chain = FilterChain(
                [
                    # Block sites that return 403 errors
                    DomainFilter(
                        blocked_domains=[
                            "constructionweekonline.com",
                            "influencedigest.com",
                            "metropolitan.realestate",
                        ]
                    ),
                    # Only include specific content types
                    ContentTypeFilter(allowed_types=["text/html"]),
                ]
            )

            # Pruning filter to remove low-relevance content
            self._prune_filter = PruningContentFilter(
                threshold=0.50,
                threshold_type="dynamic",
            )

            # Markdown generator with specific options
            self._md_generator = DefaultMarkdownGenerator(
                content_filter=self._prune_filter,
                options={
                    "ignore_links": True,
                    "escape_html": True,
                    "skip_internal_links": True,
                    "body_width": 0,
                },
            )

            self._config = CrawlerRunConfig(
                excluded_tags=["nav", "header", "footer", "script", "style"],
                exclude_external_links=True,
                exclude_internal_links=True,
                preserve_https_for_internal_links=True,
                verbose=True,
                deep_crawl_strategy=DFSDeepCrawlStrategy(
                    max_depth=1,
                    max_pages=1,
                    include_external=False,
                    filter_chain=self._filter_chain,
                ),
                scraping_strategy=LXMLWebScrapingStrategy(),
                markdown_generator=self._md_generator,
            )

            self._crawler = AsyncWebCrawler(
                config=self._browser_config,
                crawler_strategy=self._strategy,
                timeout=self.timeout,
            )

            await self._crawler.start()

            console.print("[green]Crawl4AI crawler ready[/green]")

        return self._crawler

    async def crawl(self, url: str) -> Dict:
        logger.info("Crawling URL: %s", url)
        console.print(f"[cyan]→ Crawling[/cyan] {url}")

        # Check if URL is a PDF
        is_pdf = await self._is_pdf_url(url)

        try:
            crawler = await self._get_crawler()

            if is_pdf:
                # Handle PDF URLs with specific PDF processing
                pdf_config = CrawlerRunConfig(
                    scraping_strategy=PDFContentScrapingStrategy(
                        extract_images=False, batch_size=4
                    ),
                    verbose=True,
                )

                # Use PDF-specific crawler strategy
                pdf_crawler = AsyncWebCrawler(
                    config=self._browser_config,
                    crawler_strategy=PDFCrawlerStrategy(),
                    timeout=self.timeout,
                )
                await pdf_crawler.start()

                result = await pdf_crawler.arun(url=url, config=pdf_config)

                await pdf_crawler.close()

                results = [result]

            else:
                # Handle regular HTML URLs with existing configuration
                results = await crawler.arun(url=url, config=self._config)

            for result in results:
                if not result.success:
                    logger.warning("Empty or invalid crawl result for %s", url)
                    logger.info(f"Status code: {result.status_code}")
                    logger.info(f"Failed to crawl {result.url}: {result.error_message}")
                    console.print("[yellow]Warning: empty content returned[/yellow]")

                    return {
                        "url": url,
                        "title": None,
                        "content": None,
                        "published_at": None,
                        "author": None,
                        "error": "Empty content",
                    }
                else:
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
                        "content": result.markdown.fit_markdown,
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

    async def _is_pdf_url(self, url: str) -> bool:
        """
        Check if the given URL points to a PDF file.
        True if the URL appears to be a PDF, False otherwise.
        """
        parsed_url = urlparse(url)
        path = parsed_url.path.lower()
        return path.endswith(".pdf")
