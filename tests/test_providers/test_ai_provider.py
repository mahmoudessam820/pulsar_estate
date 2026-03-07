import json
import pytest
import httpx
from unittest.mock import AsyncMock, Mock, patch


from app.providers.ai.ollama import OllamaCloudProvider


class TestOllamaCloudProviderInit:
    """Tests for __init__ method."""

    def test_init_with_defaults(self):
        provider = OllamaCloudProvider()
        assert provider.model == "qwen3-vl:235b-instruct-cloud"
        assert provider.temperature == 0.2

    def test_init_with_custom_params(self):
        provider = OllamaCloudProvider(model="test-model", temperature=0.8)
        assert provider.model == "test-model"
        assert provider.temperature == 0.8

    @patch("app.providers.ai.ollama.settings")
    def test_init_loads_settings(self, mock_settings):
        mock_settings.ollama_base_url = "http://ollama.test"
        mock_settings.ollama_api_key = "sk-test123"

        provider = OllamaCloudProvider()

        assert provider.base_url == "http://ollama.test"
        assert provider.api_key == "sk-test123"


class TestBuildPrompt:
    """Tests for _build_prompt method."""

    def test_build_prompt_with_valid_documents(self):
        provider = OllamaCloudProvider()
        documents = [
            {
                "url": "https://example.com/article-1",
                "title": "Dubai Market Update",
                "published_at": "2024-01-15",
                "content": "Property prices increased by 5%",
            }
        ]

        prompt = provider._build_prompt(documents)

        assert "Analyze the following real estate articles" in prompt
        assert "https://example.com/article-1" in prompt
        assert "Dubai Market Update" in prompt
        assert "Property prices increased by 5%" in prompt

    def test_build_prompt_filters_docs_without_content(self):
        provider = OllamaCloudProvider()
        documents = [
            {"url": "https://ex.com/1", "title": "No Content Doc"},
            {"url": "https://ex.com/2", "content": "Valid content"},
            {"url": "https://ex.com/3", "content": ""},
        ]

        prompt = provider._build_prompt(documents)

        assert "https://ex.com/1" not in prompt
        assert "https://ex.com/2" in prompt
        assert "Valid content" in prompt
        assert "https://ex.com/3" not in prompt

    def test_build_prompt_empty_list(self):
        provider = OllamaCloudProvider()
        prompt = provider._build_prompt([])

        assert "Analyze the following real estate articles" in prompt


class TestParseResponse:
    """Tests for _parse_response method."""

    def test_parse_response_valid_json(self):
        provider = OllamaCloudProvider()
        content = json.dumps(
            {
                "summary": "Test summary",
                "key_trends": ["trend1"],
                "market_sentiment": "positive",
            }
        )

        result = provider._parse_response(content)

        assert result["summary"] == "Test summary"
        assert "error" not in result

    def test_parse_response_invalid_json(self):
        provider = OllamaCloudProvider()
        content = "This is not JSON at all"

        result = provider._parse_response(content)

        assert "error" in result
        assert result["error"] == "Invalid JSON from AI"
        assert result["raw_output"] == content


@pytest.mark.asyncio
class TestAnalyze:
    """Tests for async analyze method."""

    @patch("app.providers.ai.ollama.settings")
    async def test_analyze_success_valid_response(self, mock_settings):
        """Normal case: successful API call with valid JSON."""
        mock_settings.ollama_base_url = "http://test.api"
        mock_settings.ollama_api_key = "test-key"

        provider = OllamaCloudProvider()
        documents = [{"url": "https://ex.com", "content": "test content"}]

        # Use Mock (not AsyncMock) for response - httpx.Response.json() is sync
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "summary": "Market analysis",
                                "key_trends": ["upward"],
                                "market_sentiment": "positive",
                                "evidence": [],
                            }
                        )
                    }
                }
            ]
        }

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            # post() is async, so return the sync Mock response
            mock_client.post.return_value = mock_response
            mock_client_cls.return_value = mock_client

            result = await provider.analyze(documents)

            assert result["summary"] == "Market analysis"
            assert result["market_sentiment"] == "positive"
            assert "error" not in result

    @patch("app.providers.ai.ollama.settings")
    async def test_analyze_invalid_json_from_api(self, mock_settings):
        """Edge case: API returns non-JSON content."""
        mock_settings.ollama_base_url = "http://test.api"
        mock_settings.ollama_api_key = "test-key"

        provider = OllamaCloudProvider()
        documents = [{"url": "https://ex.com", "content": "test"}]

        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "not valid json"}}]
        }

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.post.return_value = mock_response
            mock_client_cls.return_value = mock_client

            result = await provider.analyze(documents)

            assert "error" in result
            assert result["error"] == "Invalid JSON from AI"

    @patch("app.providers.ai.ollama.settings")
    async def test_analyze_http_status_error(self, mock_settings):
        """Edge case: HTTP error (4xx/5xx)."""
        mock_settings.ollama_base_url = "http://test.api"
        mock_settings.ollama_api_key = "test-key"

        provider = OllamaCloudProvider()
        documents = [{"url": "https://ex.com", "content": "test"}]

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client

            mock_request = Mock()
            mock_resp = Mock(status_code=429, text="Rate limit exceeded")
            mock_client.post.side_effect = httpx.HTTPStatusError(
                "Rate limit exceeded", request=mock_request, response=mock_resp
            )
            mock_client_cls.return_value = mock_client

            result = await provider.analyze(documents)

            assert "error" in result
            assert "HTTP 429" in result["error"]

    @patch("app.providers.ai.ollama.settings")
    async def test_analyze_unexpected_exception(self, mock_settings):
        """Edge case: unexpected network/connection error."""
        mock_settings.ollama_base_url = "http://test.api"
        mock_settings.ollama_api_key = "test-key"

        provider = OllamaCloudProvider()
        documents = [{"url": "https://ex.com", "content": "test"}]

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.post.side_effect = ConnectionError("Network down")
            mock_client_cls.return_value = mock_client

            result = await provider.analyze(documents)

            assert "error" in result
            assert "Network down" in result["error"]

    @patch("app.providers.ai.ollama.settings")
    async def test_analyze_empty_documents_list(self, mock_settings):
        """Edge case: empty documents list."""
        mock_settings.ollama_base_url = "http://test.api"
        mock_settings.ollama_api_key = "test-key"

        provider = OllamaCloudProvider()

        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": json.dumps({"summary": "No data"})}}]
        }

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.post.return_value = mock_response
            mock_client_cls.return_value = mock_client

            result = await provider.analyze([])

            assert mock_client.post.called
            assert isinstance(result, dict)

    @patch("app.providers.ai.ollama.settings")
    async def test_analyze_docs_missing_content_field(self, mock_settings):
        """Invalid input: documents without required content field."""
        mock_settings.ollama_base_url = "http://test.api"
        mock_settings.ollama_api_key = "test-key"

        provider = OllamaCloudProvider()
        documents = [
            {"url": "https://ex.com/1", "title": "No content"},
            {"url": "https://ex.com/2"},
        ]

        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": json.dumps({"summary": "Empty"})}}]
        }

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.post.return_value = mock_response
            mock_client_cls.return_value = mock_client

            result = await provider.analyze(documents)

            assert mock_client.post.called
            assert isinstance(result, dict)
