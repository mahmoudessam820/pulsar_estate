import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from datetime import datetime

from app.providers.crawler.crawl4ai import Crawl4AIProvider


class TestCrawl4AIProviderInit:
    """Tests for __init__ method."""

    def test_init_with_default_timeout(self):
        provider = Crawl4AIProvider()
        assert provider.timeout == 20
        assert provider._crawler is None

    def test_init_with_custom_timeout(self):
        provider = Crawl4AIProvider(timeout=45)
        assert provider.timeout == 45


class TestIsPdfUrl:
    """Tests for _is_pdf_url method."""

    @pytest.mark.asyncio
    async def test_is_pdf_url_true(self):
        provider = Crawl4AIProvider()
        assert await provider._is_pdf_url("https://example.com/report.pdf") is True
        assert await provider._is_pdf_url("https://example.com/file.PDF") is True

    @pytest.mark.asyncio
    async def test_is_pdf_url_false(self):
        provider = Crawl4AIProvider()
        assert await provider._is_pdf_url("https://example.com/article") is False
        assert (
            await provider._is_pdf_url("https://example.com/doc.pdf?download=1") is True
        )
        assert (
            await provider._is_pdf_url("https://example.com/pdf-report.html") is False
        )


class TestExtractDatesFromContent:
    """Tests for _extract_dates_from_content method."""

    def setup_method(self):
        self.provider = Crawl4AIProvider()

    def test_extract_date_yyyy_mm_dd(self):
        content = "Published: 2025-03-15 - Market update"
        result = self.provider._extract_dates_from_content(content)

        assert result is not None
        assert result.year == 2025
        assert result.month == 3
        assert result.day == 15

    def test_extract_date_month_dd_yyyy(self):
        content = "Posted: March 15, 2025 - Dubai real estate news"
        result = self.provider._extract_dates_from_content(content)

        assert result is not None
        assert result.year == 2025

    def test_extract_date_dd_month_yyyy(self):
        content = "15 March 2025: Property prices rise"
        result = self.provider._extract_dates_from_content(content)

        assert result is not None
        assert result.year == 2025

    def test_extract_date_abbreviated_month(self):
        content = "Updated: Mar 15, 2025"
        result = self.provider._extract_dates_from_content(content)
        assert result is not None

    def test_extract_date_multiple_returns_earliest(self):
        content = "2026-01-01 and 2025-03-15 both mentioned"
        result = self.provider._extract_dates_from_content(content)
        # Should return earliest (min) date
        assert result.year == 2025

    def test_extract_date_no_valid_dates(self):
        content = "No dates here, just text about real estate"
        result = self.provider._extract_dates_from_content(content)
        assert result is None

    def test_extract_date_empty_content(self):
        result = self.provider._extract_dates_from_content("")
        assert result is None

    def test_extract_date_out_of_range_year_ignored(self):
        content = "Historical data from 1985-01-01 and future 2035-01-01"
        result = self.provider._extract_dates_from_content(content)
        # Both years outside 2025-2026 range, should return None
        assert result is None


@pytest.mark.asyncio
class TestGetCrawler:
    """Tests for _get_crawler lazy initialization."""

    @patch("app.providers.crawler.crawl4ai.AsyncWebCrawler")
    @patch("app.providers.crawler.crawl4ai.BrowserConfig")
    @patch("app.providers.crawler.crawl4ai.UndetectedAdapter")
    @patch("app.providers.crawler.crawl4ai.AsyncPlaywrightCrawlerStrategy")
    async def test_get_crawler_initializes_once(
        self, mock_strategy, mock_adapter, mock_browser_config, mock_crawler_cls
    ):
        provider = Crawl4AIProvider()

        # Setup mocks
        mock_crawler = AsyncMock()
        mock_crawler_cls.return_value = mock_crawler

        # First call
        crawler1 = await provider._get_crawler()
        assert mock_crawler_cls.called
        assert mock_crawler.start.called

        # Reset call count
        mock_crawler_cls.reset_mock()
        mock_crawler.start.reset_mock()

        # Second call should reuse existing crawler
        crawler2 = await provider._get_crawler()

        assert crawler1 is crawler2
        assert not mock_crawler_cls.called  # Not re-initialized
        assert not mock_crawler.start.called

    @patch("app.providers.crawler.crawl4ai.AsyncWebCrawler")
    async def test_get_crawler_configures_components(self, mock_crawler_cls):
        provider = Crawl4AIProvider(timeout=30)

        mock_crawler = AsyncMock()
        mock_crawler_cls.return_value = mock_crawler

        await provider._get_crawler()

        # Verify crawler was created with expected params
        call_kwargs = mock_crawler_cls.call_args[1]
        assert call_kwargs["timeout"] == 30
        assert mock_crawler.start.called


@pytest.mark.asyncio
class TestCrawl:
    """Tests for crawl method."""

    @patch("app.providers.crawler.crawl4ai.Crawl4AIProvider._is_pdf_url")
    @patch("app.providers.crawler.crawl4ai.Crawl4AIProvider._get_crawler")
    async def test_crawl_html_success(self, mock_get_crawler, mock_is_pdf):
        """Normal case: successful HTML crawl."""
        mock_is_pdf.return_value = False

        mock_crawler = AsyncMock()
        mock_get_crawler.return_value = mock_crawler

        mock_markdown = MagicMock()
        mock_markdown.fit_markdown = "## Title\nContent here"

        mock_result = Mock()
        mock_result.success = True
        mock_result.markdown = mock_markdown
        mock_result.metadata = {
            "title": "Test Article",
            "published_date": "2025-03-15",
            "author": "John Doe",
        }

        mock_crawler.arun.return_value = [mock_result]

        provider = Crawl4AIProvider()
        result = await provider.crawl("https://example.com/article")

        assert result["url"] == "https://example.com/article"
        assert result["title"] == "Test Article"
        assert result["content"] == "## Title\nContent here"
        assert result["published_at"] == "2025-03-15"
        assert result["author"] == "John Doe"
        assert result["error"] is None

    @patch("app.providers.crawler.crawl4ai.Crawl4AIProvider._is_pdf_url")
    @patch("app.providers.crawler.crawl4ai.Crawl4AIProvider._get_crawler")
    @patch(
        "app.providers.crawler.crawl4ai.Crawl4AIProvider._extract_dates_from_content"
    )
    async def test_crawl_html_missing_metadata_extracted_from_content(
        self, mock_extract_dates, mock_get_crawler, mock_is_pdf
    ):
        """Edge case: metadata missing, date extracted from content."""
        mock_is_pdf.return_value = False

        # Mock date extraction to return a known date
        mock_extract_dates.return_value = datetime(2025, 3, 15)

        mock_crawler = AsyncMock()
        mock_get_crawler.return_value = mock_crawler

        mock_markdown = MagicMock()
        mock_markdown.fit_markdown = "Published: March 15, 2025\n## Content"

        mock_result = Mock()
        mock_result.success = True
        mock_result.markdown = mock_markdown
        # No published_date in metadata - triggers fallback
        mock_result.metadata = {"title": "No Date Article"}

        mock_crawler.arun.return_value = [mock_result]

        provider = Crawl4AIProvider()
        result = await provider.crawl("https://example.com/article")

        # Verify fallback was called with markdown object
        mock_extract_dates.assert_called_once()
        assert result["published_at"] == datetime(2025, 3, 15)

    @patch("app.providers.crawler.crawl4ai.Crawl4AIProvider._is_pdf_url")
    @patch("app.providers.crawler.crawl4ai.Crawl4AIProvider._get_crawler")
    async def test_crawl_html_failed_result(self, mock_get_crawler, mock_is_pdf):
        """Edge case: crawl result indicates failure."""
        mock_is_pdf.return_value = False

        mock_crawler = AsyncMock()
        mock_get_crawler.return_value = mock_crawler

        mock_result = Mock()
        mock_result.success = False
        mock_result.status_code = 404
        mock_result.error_message = "Not found"
        mock_result.url = "https://example.com/missing"

        mock_crawler.arun.return_value = [mock_result]

        provider = Crawl4AIProvider()
        result = await provider.crawl("https://example.com/missing")

        assert result["error"] == "Empty content"
        assert result["content"] is None

    @patch("app.providers.crawler.crawl4ai.Crawl4AIProvider._is_pdf_url")
    async def test_crawl_pdf_success(self, mock_is_pdf):
        """Normal case: successful PDF crawl."""
        mock_is_pdf.return_value = True

        with (
            patch("app.providers.crawler.crawl4ai.AsyncWebCrawler") as mock_crawler_cls,
            patch("app.providers.crawler.crawl4ai.PDFContentScrapingStrategy"),
            patch("app.providers.crawler.crawl4ai.PDFCrawlerStrategy"),
            patch("app.providers.crawler.crawl4ai.BrowserConfig"),
        ):
            mock_crawler = AsyncMock()
            mock_crawler_cls.return_value = mock_crawler

            mock_markdown = MagicMock()
            mock_markdown.raw_markdown = "# PDF Content\nExtracted text"

            mock_result = Mock()
            mock_result.markdown = mock_markdown

            mock_crawler.arun.return_value = mock_result

            provider = Crawl4AIProvider()
            result = await provider.crawl("https://example.com/report.pdf")

            assert result["url"] == "https://example.com/report.pdf"
            assert "PDF Content" in result["content"]

    @patch("app.providers.crawler.crawl4ai.Crawl4AIProvider._is_pdf_url")
    async def test_crawl_pdf_empty_content(self, mock_is_pdf):
        """Edge case: PDF crawl returns empty content."""
        mock_is_pdf.return_value = True

        with (
            patch("app.providers.crawler.crawl4ai.AsyncWebCrawler") as mock_crawler_cls,
            patch("app.providers.crawler.crawl4ai.PDFContentScrapingStrategy"),
            patch("app.providers.crawler.crawl4ai.PDFCrawlerStrategy"),
            patch("app.providers.crawler.crawl4ai.BrowserConfig"),
        ):
            mock_crawler = AsyncMock()
            mock_crawler_cls.return_value = mock_crawler

            mock_result = Mock()
            mock_result.markdown = None

            mock_crawler.arun.return_value = mock_result

            provider = Crawl4AIProvider()
            result = await provider.crawl("https://example.com/empty.pdf")

            assert result["error"] == "Empty content from PDF crawl"
            assert result["content"] is None

    @patch("app.providers.crawler.crawl4ai.Crawl4AIProvider._is_pdf_url")
    @patch("app.providers.crawler.crawl4ai.Crawl4AIProvider._get_crawler")
    async def test_crawl_unexpected_exception(self, mock_get_crawler, mock_is_pdf):
        """Edge case: unexpected error during crawl."""
        mock_is_pdf.return_value = False
        mock_get_crawler.side_effect = ConnectionError("Network failed")

        provider = Crawl4AIProvider()
        result = await provider.crawl("https://example.com/article")

        assert "error" in result
        assert "Network failed" in result["error"]
        assert result["content"] is None

    @patch("app.providers.crawler.crawl4ai.Crawl4AIProvider._is_pdf_url")
    @patch("app.providers.crawler.crawl4ai.Crawl4AIProvider._get_crawler")
    async def test_crawl_invalid_url_format(self, mock_get_crawler, mock_is_pdf):
        """Invalid input: malformed URL."""
        mock_is_pdf.return_value = False

        mock_crawler = AsyncMock()
        mock_get_crawler.return_value = mock_crawler
        mock_crawler.arun.side_effect = ValueError("Invalid URL")

        provider = Crawl4AIProvider()
        result = await provider.crawl("not-a-valid-url")

        assert "error" in result
        assert result["content"] is None


@pytest.mark.asyncio
class TestClose:
    """Tests for close method."""

    @patch("app.providers.crawler.crawl4ai.AsyncWebCrawler")
    async def test_close_when_crawler_exists(self, mock_crawler_cls):
        """Normal case: close initialized crawler."""
        mock_crawler = AsyncMock()
        mock_crawler_cls.return_value = mock_crawler

        provider = Crawl4AIProvider()
        await provider._get_crawler()
        await provider.close()

        assert mock_crawler.close.called
        assert provider._crawler is None

    @pytest.mark.asyncio
    async def test_close_when_crawler_not_initialized(self):
        """Edge case: close without initialization."""
        provider = Crawl4AIProvider()
        await provider.close()
        assert provider._crawler is None
