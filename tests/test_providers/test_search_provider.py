import pytest
from unittest.mock import patch, MagicMock


from app.providers.search.duckduckgo import DuckDuckGoSearchProvider
from app.providers.search.utils import normalize_query, has_meaningful_content


class TestNormalizeQuery:
    def test_normal_input_appends_keywords(self):
        """Test that a normal query gets base keywords appended."""
        query = "luxury villas"
        result = normalize_query(query)

        assert result.startswith("luxury villas ")
        assert "Dubai real estate" in result
        assert "property market" in result

    def test_empty_string_input(self):
        """Test behavior with an empty string."""
        result = normalize_query("")
        # Should still append keywords even if input is empty
        assert result.startswith(" ")
        assert "Dubai real estate" in result

    def test_whitespace_only_input(self):
        """Test behavior with whitespace only."""
        result = normalize_query("   ")
        assert "Dubai real estate" in result

    def test_special_characters_in_query(self):
        """Test that special characters in query are preserved."""
        query = "price $1M+"
        result = normalize_query(query)
        assert result.startswith("price $1M+ ")
        assert "Dubai real estate" in result


class TestHasMeaningfulContent:
    @pytest.mark.parametrize(
        "url, expected",
        [
            # Valid cases
            ("https://example.com/path", True),
            ("https://example.com/path/to/page", True),
            ("https://example.com/?query=param", True),
            ("https://example.com#fragment", True),
            ("https://example.com/path?query=1#frag", True),
            ("http://test.org/article/123", True),
            # Invalid / Root cases
            ("https://example.com/", False),
            ("https://example.com", False),
            ("https://example.com/   ", False),  # Whitespace path
            ("   https://example.com   ", False),  # Whitespace around domain
            ("", False),
            ("   ", False),
            # Malformed cases
            ("example.com/path", False),  # Missing scheme
            ("https:///path", False),  # Missing domain
            ("not-a-url", False),
            ("ftp://files.com/", False),  # Root path on valid scheme
        ],
    )
    def test_url_validation(self, url, expected):
        assert has_meaningful_content(url) == expected


class TestDuckDuckGoSearchProvider:
    @pytest.fixture
    def provider(self):
        return DuckDuckGoSearchProvider(max_results=25)

    # Patch paths must point to where the names are LOOKED UP (the module using them)
    @pytest.mark.asyncio
    @patch("app.providers.search.duckduckgo.DDGS")
    @patch("app.providers.search.duckduckgo.normalize_query")
    @patch("app.providers.search.duckduckgo.has_meaningful_content")
    @patch("app.providers.search.duckduckgo.Console")
    async def test_search_success_with_results(
        self,
        mock_console_cls,
        mock_has_content,
        mock_normalize,
        mock_ddgs_cls,
        provider,
    ):
        """Test successful search returning filtered URLs."""
        # Setup mocks
        mock_normalize.return_value = "normalized query"

        # Filter out the bad URL
        mock_has_content.side_effect = lambda url: url != "https://bad.com"

        # Mock DDGS context manager
        mock_ddgs_instance = MagicMock()
        mock_ddgs_cls.return_value.__enter__.return_value = mock_ddgs_instance
        mock_ddgs_cls.return_value.__exit__.return_value = None

        mock_results = [
            {"href": "https://good.com/1"},
            {"href": "https://bad.com"},  # Filtered
            {"href": "https://good.com/2"},
            {"href": None},  # Skipped
        ]
        mock_ddgs_instance.text.return_value = mock_results

        # AWAIT the async method
        result = await provider.search("test query")

        # Assertions
        mock_normalize.assert_called_once_with("test query")
        assert mock_has_content.call_count == 3
        assert result == ["https://good.com/1", "https://good.com/2"]
        assert len(result) == 2

    @pytest.mark.asyncio
    @patch("app.providers.search.duckduckgo.DDGS")
    @patch("app.providers.search.duckduckgo.normalize_query")
    @patch("app.providers.search.duckduckgo.Console")
    async def test_search_no_results(
        self, mock_console_cls, mock_normalize, mock_ddgs_cls, provider
    ):
        """Test search when no results are returned."""
        mock_normalize.return_value = "normalized query"

        mock_ddgs_instance = MagicMock()
        mock_ddgs_cls.return_value.__enter__.return_value = mock_ddgs_instance
        mock_ddgs_cls.return_value.__exit__.return_value = None
        mock_ddgs_instance.text.return_value = []

        result = await provider.search("empty query")

        assert result == []
        mock_ddgs_instance.text.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.providers.search.duckduckgo.DDGS")
    @patch("app.providers.search.duckduckgo.normalize_query")
    @patch("app.providers.search.duckduckgo.has_meaningful_content")
    @patch("app.providers.search.duckduckgo.Console")
    async def test_search_all_results_filtered(
        self,
        mock_console_cls,
        mock_has_content,
        mock_normalize,
        mock_ddgs_cls,
        provider,
    ):
        """Test search when all results are filtered out."""
        mock_normalize.return_value = "normalized query"
        mock_has_content.return_value = False

        mock_ddgs_instance = MagicMock()
        mock_ddgs_cls.return_value.__enter__.return_value = mock_ddgs_instance
        mock_ddgs_cls.return_value.__exit__.return_value = None
        mock_ddgs_instance.text.return_value = [{"href": "https://spam.com"}]

        result = await provider.search("spam query")

        assert result == []
