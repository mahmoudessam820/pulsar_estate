import pytest

from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import HTTPException

from app.api.routes.admin import router, verify_admin_key, settings
from app.core.pipeline.factory import build_pipeline
from app.core.pipeline.pipeline_service import PipelineService


# Create test client
def create_test_client():
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


# Build Pipeline Tests
class TestBuildPipeline:
    def test_build_pipeline_returns_pipeline_service(self):
        result = build_pipeline()

        assert isinstance(result, PipelineService)

    def test_build_pipeline_injects_correct_providers(self):
        result = build_pipeline()

        # Check providers are instantiated (type check)
        from app.providers.search.duckduckgo import DuckDuckGoSearchProvider
        from app.providers.crawler.crawl4ai import Crawl4AIProvider
        from app.providers.ai.ollama import OllamaCloudProvider
        from app.data.repositories.insight_repo import JSONInsightRepository

        assert isinstance(result.search_provider, DuckDuckGoSearchProvider)
        assert isinstance(result.crawl_provider, Crawl4AIProvider)
        assert isinstance(result.ai_provider, OllamaCloudProvider)
        assert isinstance(result.insight_repository, JSONInsightRepository)

    def test_build_pipeline_creates_new_instance_each_call(self):
        pipeline1 = build_pipeline()
        pipeline2 = build_pipeline()
        assert pipeline1 is not pipeline2


# Admin Key Verification Tests
class TestVerifyAdminKey:
    def test_verify_admin_key_valid(self):
        # Valid key matches settings
        result = verify_admin_key(x_admin_key=settings.admin_api_key)
        assert result is None  # No exception means success

    def test_verify_admin_key_invalid(self):
        with pytest.raises(HTTPException) as exc_info:
            verify_admin_key(x_admin_key="wrong-key")

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Unauthorized"

    def test_verify_admin_key_empty_string(self):
        with pytest.raises(HTTPException) as exc_info:
            verify_admin_key(x_admin_key="")

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Unauthorized"

    def test_verify_admin_key_none_value(self):
        # Header(...) would raise a validation error before our function,
        # but we test the function directly with None
        with pytest.raises(HTTPException):
            verify_admin_key(x_admin_key=None)


# Run Pipeline Endpoint Tests
class TestRunPipelineEndpoint:
    @pytest.mark.asyncio
    async def test_run_pipeline_success(self):
        mock_pipeline = AsyncMock(spec=PipelineService)
        mock_pipeline.run = AsyncMock(return_value=None)
        mock_pipeline.close = AsyncMock(return_value=None)

        with patch("app.api.routes.admin.build_pipeline", return_value=mock_pipeline):
            client = create_test_client()
            response = client.post(
                "/pipeline/run", headers={"x-admin-key": settings.admin_api_key}
            )

            assert response.status_code == 200
            mock_pipeline.run.assert_called_once_with("Dubai real estate market trends")
            mock_pipeline.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_pipeline_exception_handling(self):
        mock_pipeline = AsyncMock(spec=PipelineService)
        mock_pipeline.run = AsyncMock(side_effect=Exception("Pipeline failed"))
        mock_pipeline.close = AsyncMock(return_value=None)

        with patch("app.api.routes.admin.build_pipeline", return_value=mock_pipeline):
            client = create_test_client()
            response = client.post(
                "/pipeline/run", headers={"x-admin-key": settings.admin_api_key}
            )

            assert response.status_code == 500
            assert "Pipeline failed" in response.json()["detail"]
            mock_pipeline.close.assert_called_once()  # finally block still runs

    @pytest.mark.asyncio
    async def test_run_pipeline_close_called_on_exception(self):
        """Ensure close() is called even when run() raises"""
        mock_pipeline = AsyncMock(spec=PipelineService)
        mock_pipeline.run = AsyncMock(side_effect=ConnectionError("DB error"))
        mock_pipeline.close = AsyncMock(return_value=None)

        with patch("app.api.routes.admin.build_pipeline", return_value=mock_pipeline):
            client = create_test_client()
            client.post(
                "/pipeline/run", headers={"x-admin-key": settings.admin_api_key}
            )

            mock_pipeline.close.assert_called_once()


# Authentication Tests
class TestAuthentication:
    @pytest.mark.asyncio
    async def test_run_pipeline_without_admin_key(self):
        client = create_test_client()
        response = client.post("/pipeline/run")

        # FastAPI returns 422 for missing required header
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_run_pipeline_with_wrong_admin_key(self):
        client = create_test_client()
        response = client.post("/pipeline/run", headers={"x-admin-key": "wrong-key"})

        assert response.status_code == 401
        assert response.json()["detail"] == "Unauthorized"

    @pytest.mark.asyncio
    async def test_run_pipeline_with_correct_admin_key(self):
        mock_pipeline = AsyncMock(spec=PipelineService)
        mock_pipeline.run = AsyncMock(return_value=None)
        mock_pipeline.close = AsyncMock(return_value=None)

        with patch("app.api.routes.admin.build_pipeline", return_value=mock_pipeline):
            client = create_test_client()
            response = client.post(
                "/pipeline/run", headers={"x-admin-key": settings.admin_api_key}
            )

            assert response.status_code == 200


# Edge Cases
class TestEdgeCases:
    @pytest.mark.asyncio
    async def test_run_pipeline_with_special_chars_in_error(self):
        mock_pipeline = AsyncMock(spec=PipelineService)
        error_msg = "Error: <script>alert('xss')</script>"
        mock_pipeline.run = AsyncMock(side_effect=Exception(error_msg))
        mock_pipeline.close = AsyncMock(return_value=None)

        with patch("app.api.routes.admin.build_pipeline", return_value=mock_pipeline):
            client = create_test_client()
            response = client.post(
                "/pipeline/run", headers={"x-admin-key": settings.admin_api_key}
            )

            assert response.status_code == 500
            # Error message is returned as-is (FastAPI handles escaping)
            assert error_msg in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_run_pipeline_multiple_times(self):
        mock_pipeline = AsyncMock(spec=PipelineService)
        mock_pipeline.run = AsyncMock(return_value=None)
        mock_pipeline.close = AsyncMock(return_value=None)

        with patch("app.api.routes.admin.build_pipeline", return_value=mock_pipeline):
            client = create_test_client()

            response1 = client.post(
                "/pipeline/run", headers={"x-admin-key": settings.admin_api_key}
            )
            response2 = client.post(
                "/pipeline/run", headers={"x-admin-key": settings.admin_api_key}
            )

            assert response1.status_code == 200
            assert response2.status_code == 200
            # build_pipeline is called each time, creating new instances
            assert mock_pipeline.run.call_count == 2

    @pytest.mark.asyncio
    async def test_run_pipeline_case_insensitive_admin_key(self):
        # Settings uses case_sensitive=False, but header comparison is exact
        mock_pipeline = AsyncMock(spec=PipelineService)
        mock_pipeline.run = AsyncMock(return_value=None)
        mock_pipeline.close = AsyncMock(return_value=None)

        with patch("app.api.routes.admin.build_pipeline", return_value=mock_pipeline):
            client = create_test_client()

            # Exact match required (case-sensitive string comparison)
            response = client.post(
                "/pipeline/run", headers={"x-admin-key": settings.admin_api_key.upper()}
            )

            # This should fail because string comparison is case-sensitive
            assert response.status_code == 401


# Invalid Inputs / Error Handling
class TestErrorHandling:
    @pytest.mark.asyncio
    async def test_run_pipeline_close_raises(self):
        """Ensure exception in close() is handled"""
        mock_pipeline = AsyncMock(spec=PipelineService)
        mock_pipeline.run = AsyncMock(return_value=None)
        mock_pipeline.close = AsyncMock(side_effect=Exception("Close failed"))

        with patch("app.api.routes.admin.build_pipeline", return_value=mock_pipeline):
            client = create_test_client()
            # Exception in finally block propagates
            with pytest.raises(Exception, match="Close failed"):
                client.post(
                    "/pipeline/run", headers={"x-admin-key": settings.admin_api_key}
                )

    @pytest.mark.asyncio
    async def test_run_pipeline_timeout_error(self):
        mock_pipeline = AsyncMock(spec=PipelineService)
        mock_pipeline.run = AsyncMock(side_effect=TimeoutError("Request timed out"))
        mock_pipeline.close = AsyncMock(return_value=None)

        with patch("app.api.routes.admin.build_pipeline", return_value=mock_pipeline):
            client = create_test_client()
            response = client.post(
                "/pipeline/run", headers={"x-admin-key": settings.admin_api_key}
            )

            assert response.status_code == 500
            assert "Request timed out" in response.json()["detail"]


# Router Configuration Tests
class TestRouterConfiguration:
    def test_router_prefix(self):
        assert router.prefix == "/pipeline"

    def test_router_tags(self):
        assert "Pipeline" in router.tags

    def test_run_pipeline_endpoint_exists(self):
        routes = [route.path for route in router.routes]
        assert "/pipeline/run" in routes

    def test_run_pipeline_endpoint_methods(self):
        for route in router.routes:
            if route.path == "/pipeline/run":
                assert "POST" in route.methods

    def test_run_pipeline_has_auth_dependency(self):
        for route in router.routes:
            if route.path == "/pipeline/run":
                assert len(route.dependencies) > 0
