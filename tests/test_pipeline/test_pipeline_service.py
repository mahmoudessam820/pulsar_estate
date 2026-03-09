import pytest
from unittest.mock import MagicMock, patch, AsyncMock


from app.core.pipeline.pipeline_service import PipelineService


@pytest.fixture
def mock_search_provider():
    provider = AsyncMock()
    return provider


@pytest.fixture
def mock_crawl_provider():
    provider = AsyncMock()
    return provider


@pytest.fixture
def mock_ai_provider():
    provider = AsyncMock()
    return provider


@pytest.fixture
def mock_insight_repository():
    repo = AsyncMock()
    return repo


@pytest.fixture
def pipeline_service(
    mock_search_provider, mock_crawl_provider, mock_ai_provider, mock_insight_repository
):
    return PipelineService(
        search_provider=mock_search_provider,
        crawl_provider=mock_crawl_provider,
        ai_provider=mock_ai_provider,
        insight_repository=mock_insight_repository,
    )


class TestPipelineServiceRun:
    @pytest.mark.asyncio
    async def test_run_normal_flow_less_than_5_docs(
        self,
        pipeline_service,
        mock_search_provider,
        mock_crawl_provider,
        mock_ai_provider,
        mock_insight_repository,
    ):
        """Test normal execution with fewer than 5 documents (no confidence calculation)."""
        query = "test query"
        urls = ["http://example.com/1", "http://example.com/2"]
        docs = [
            {"url": "http://example.com/1", "content": "content 1"},
            {"url": "http://example.com/2", "content": "content 2"},
        ]
        insights = {"summary": "test summary"}

        mock_search_provider.search.return_value = urls
        mock_crawl_provider.crawl.side_effect = docs
        mock_ai_provider.analyze.return_value = insights

        result = await pipeline_service.run(query)

        mock_search_provider.search.assert_called_once_with(query)

        assert mock_crawl_provider.crawl.call_count == 2

        mock_ai_provider.analyze.assert_called_once_with(docs)
        mock_insight_repository.save.assert_called_once()

        assert result["query"] == query
        assert result["documents_collected"] == 2
        assert result["insights"] == insights
        assert "confidence" not in result["insights"]
        assert result["sources"] == ["http://example.com/1", "http://example.com/2"]

    @pytest.mark.asyncio
    @patch("app.core.pipeline.pipeline_service.calculate_confidence")
    @patch("app.core.pipeline.pipeline_service.explain_confidence")
    async def test_run_normal_flow_5_or_more_docs(
        self,
        mock_explain,
        mock_calc,
        pipeline_service,
        mock_search_provider,
        mock_crawl_provider,
        mock_ai_provider,
        mock_insight_repository,
    ):
        """Test execution with 5 or more documents (confidence calculation triggered)."""
        query = "test query"
        urls = [f"http://example.com/{i}" for i in range(5)]
        docs = [{"url": u, "content": f"content {i}"} for i, u in enumerate(urls)]
        insights = {"summary": "test summary"}

        mock_search_provider.search.return_value = urls
        mock_crawl_provider.crawl.side_effect = docs
        mock_ai_provider.analyze.return_value = insights
        mock_calc.return_value = 0.95
        mock_explain.return_value = "High confidence due to volume"

        result = await pipeline_service.run(query)

        mock_calc.assert_called_once_with(docs, insights)
        mock_explain.assert_called_once_with(0.95)

        assert result["documents_collected"] == 5
        assert result["insights"]["confidence"] == 0.95
        assert (
            result["insights"]["confidence_explanation"]
            == "High confidence due to volume"
        )

    @pytest.mark.asyncio
    async def test_run_no_urls_found(
        self, pipeline_service, mock_search_provider, mock_insight_repository
    ):
        """Edge case: Search provider returns empty list."""
        mock_search_provider.search.return_value = []

        result = await pipeline_service.run("empty query")

        mock_insight_repository.save.assert_not_called()
        assert result["error"] == "No valid documents collected"
        assert result["documents_collected"] == 0

    @pytest.mark.asyncio
    async def test_run_all_crawls_invalid(
        self,
        pipeline_service,
        mock_search_provider,
        mock_crawl_provider,
        mock_insight_repository,
    ):
        """Edge case: URLs found, but all crawls return errors or empty content."""
        mock_search_provider.search.return_value = [
            "http://bad.com/1",
            "http://bad.com/2",
        ]
        mock_crawl_provider.crawl.side_effect = [
            {"url": "http://bad.com/1", "error": "Timeout"},
            {"url": "http://bad.com/2", "content": ""},
        ]

        result = await pipeline_service.run("bad query")

        mock_insight_repository.save.assert_not_called()
        assert result["error"] == "No valid documents collected"
        assert result["documents_collected"] == 0

    @pytest.mark.asyncio
    async def test_run_mixed_valid_invalid_docs(
        self,
        pipeline_service,
        mock_search_provider,
        mock_crawl_provider,
        mock_ai_provider,
    ):
        """Edge case: Some docs valid, some invalid. Only valid ones processed."""
        mock_search_provider.search.return_value = [
            "http://good.com",
            "http://bad.com",
            "http://good2.com",
        ]
        mock_crawl_provider.crawl.side_effect = [
            {"url": "http://good.com", "content": "valid"},
            {"url": "http://bad.com", "error": "404"},
            {"url": "http://good2.com", "content": "valid2"},
        ]
        mock_ai_provider.analyze.return_value = {"summary": "ok"}

        result = await pipeline_service.run("query")

        assert result["documents_collected"] == 2
        assert result["sources"] == ["http://good.com", "http://good2.com"]


class TestPipelineServiceClose:
    @pytest.mark.asyncio
    async def test_close_with_close_method(self):
        """Test close() when provider has close method."""
        mock_crawl = AsyncMock()
        # Ensure the mock has the close attribute
        mock_crawl.close = AsyncMock()

        service = PipelineService(
            search_provider=AsyncMock(),
            crawl_provider=mock_crawl,
            ai_provider=AsyncMock(),
            insight_repository=AsyncMock(),
        )

        await service.close()
        mock_crawl.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_without_close_method(self):
        """Test close() when provider does not have close method."""
        # Create a mock without the close attribute explicitly set up as callable
        mock_crawl = MagicMock(spec=[])

        service = PipelineService(
            search_provider=AsyncMock(),
            crawl_provider=mock_crawl,
            ai_provider=AsyncMock(),
            insight_repository=AsyncMock(),
        )
        # Should not raise an error
        await service.close()
        # Verify close was not called (since it doesn't exist)

        assert not hasattr(mock_crawl, "close") or not mock_crawl.close.called
