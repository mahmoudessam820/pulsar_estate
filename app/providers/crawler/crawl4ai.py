import re
import logging
from typing import Dict
from urllib.parse import urlparse

from rich.console import Console
from dateutil import parser
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

    def _extract_dates_from_content(self, content: str) -> Optional[datetime]:
        """
        Extract publication dates from content using multiple strategies
        """
        if not content:
            return None

        # Common date patterns found in blog posts
        date_patterns = [
            # YYYY-MM-DD format
            r"\b(202[5-6][-/]\d{1,2}[-/]\d{1,2})\b",
            # DD/MM/YYYY or DD-MM-YYYY format (for 2025-2026)
            r"\b\d{1,2}[/-]\d{1,2}[/-](202[5-6])\b",
            # Month DD, YYYY format (for 2025-2026)
            r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+(202[5-6])\b",
            # DD Month YYYY format (for 2025-2026)
            r"\b\d{1,2}\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(202[5-6])\b",
            # Mon DD, YYYY format (for 2025-2026)
            r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+(202[5-6])\b",
            # DD Mon YYYY format (for 2025-2026)
            r"\b\d{1,2}\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(202[5-6])\b",
            # Month YYYY format (for cases like "Last update: January 2026")
            r"\b(Last update|Next update|Updated|Published|Released):\s*(January|February|March|April|May|June|July|August|September|October|November|December)\s+(202[5-6])\b",
            # Month YYYY without prefix (for cases like "January 2026")
            r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+(202[5-6])\b",
            # datetime or dateTime patterns
            r'\b(datetime|dateTime)\s*[=:]\s*[\'"]*(\d{4}-\d{2}-\d{2}T?\d{2}:\d{2}:\d{2})',
            # Published/March 15, 2025-2026
            r"\b(Published|Posted|Updated|Last updated|Published on):\s*(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+(202[5-6])\b",
            # Post published March 15th, 2025-2026
            r"\b(Post published|Published|Written on|Date posted|Updated):\s*\w+\s+\d{1,2}(?:st|nd|rd|th)?,\s+(202[5-6])\b",
        ]

        extracted_dates = []

        # Try regex patterns first
        for pattern in date_patterns:
            matches = re.findall(
                pattern, content[:2000], re.IGNORECASE
            )  # Limit to first 2000 chars for performance
            for match in matches:
                try:
                    # Handle tuple matches (month name groups)
                    if isinstance(match, tuple):
                        match_str = " ".join([m for m in match if m])
                    else:
                        match_str = match

                    # Clean up the match string
                    clean_match = re.sub(
                        r"(Published|Posted|Updated|Last updated|Published on|Post published|Written on|Date posted):\s*",
                        "",
                        match_str,
                        flags=re.IGNORECASE,
                    )
                    clean_match = clean_match.strip()

                    parsed_date = parser.parse(clean_match)
                    extracted_dates.append(parsed_date)
                except:
                    continue

        # If no dates found via regex, try more aggressive parsing
        if not extracted_dates:
            # Look for dates in first portion of content where publish info is likely
            content_start = content[
                :1000
            ]  # First 1000 characters should contain headers
            words = content_start.split()

            # Look for patterns like "March 15, 2024" in the beginning
            for i, word in enumerate(words):
                if i < len(words) - 2:
                    potential_phrase = " ".join(
                        words[i : i + 3]
                    )  # Check 3-word phrases
                    try:
                        # Try to parse potential date phrases
                        parsed = parser.parse(potential_phrase, fuzzy=True)
                        # Check if it looks like a reasonable date (not too old/new)
                        if 1990 <= parsed.year <= 2030:
                            extracted_dates.append(parsed)
                    except:
                        pass

        if extracted_dates:
            # Return the most recent date (assuming newer dates are more relevant)
            # Or return the earliest date (assuming first mentioned is publication date)

            return min(extracted_dates)

        return None

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

                    # Get initial metadata values
                    initial_published_at = result.metadata.get("published_date")

                    # If metadata is missing, try to extract from content
                    final_published_at = initial_published_at
                    if not final_published_at:
                        final_published_at = self._extract_dates_from_content(
                            result.markdown
                        )

                    return {
                        "url": url,
                        "title": result.metadata.get("title"),
                        "content": result.markdown.fit_markdown,
                        "published_at": final_published_at,
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
