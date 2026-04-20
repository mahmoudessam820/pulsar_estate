from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.api.routes.insights import router
from app.data.repositories.base import InsightRepositoryBase
from app.api.models.insight import InsightResponse, InsightContent, ConfidenceModel


# Create test client
def create_test_client():
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


# Helper Functions
def create_mock_insight():
    return InsightResponse(
        query="Dubai Luxury Residential Real Estate Market Size And Trends Analysis",
        documents_collected=10,
        sources=["source1", "source2"],
        insights=InsightContent(
            summary="Test summary",
            key_trends=["trend1", "trend2"],
            market_sentiment="positive",
            confidence=ConfidenceModel(
                score=0.95,
                label="high",
                badge="verified",
                source_strength=0.9,
                evidence_coverage=0.85,
                freshness=0.8,
                consensus=0.9,
                sources_count=5,
            ),
            confidence_explanation="High confidence due to multiple sources",
        ),
    )


# Endpoint Tests
class TestGetLatestInsight:
    @pytest.mark.asyncio
    async def test_get_latest_insight_success(self):
        mock_insight = create_mock_insight()

        mock_repo = AsyncMock(spec=InsightRepositoryBase)
        mock_repo.load_latest = AsyncMock(return_value=mock_insight)

        with patch(
            "app.api.routes.insights.get_insight_repository", return_value=mock_repo
        ):
            client = create_test_client()
            response = client.get("/insights/latest")

            assert response.status_code == 200
            data = response.json()
            assert (
                data["query"]
                == "Dubai Luxury Residential Real Estate Market Size And Trends Analysis"
            )
            assert data["documents_collected"] == 15
            assert len(data["sources"]) == 15


# Response Model Tests
class TestResponseModel:
    @pytest.mark.asyncio
    async def test_response_contains_all_required_fields(self):
        mock_insight = create_mock_insight()

        mock_repo = AsyncMock(spec=InsightRepositoryBase)
        mock_repo.load_latest = AsyncMock(return_value=mock_insight)

        with patch(
            "app.api.routes.insights.get_insight_repository", return_value=mock_repo
        ):
            client = create_test_client()
            response = client.get("/insights/latest")

            data = response.json()

            assert "query" in data
            assert "documents_collected" in data
            assert "sources" in data
            assert "insights" in data

    @pytest.mark.asyncio
    async def test_insight_content_fields(self):
        mock_insight = create_mock_insight()

        mock_repo = AsyncMock(spec=InsightRepositoryBase)
        mock_repo.load_latest = AsyncMock(return_value=mock_insight)

        with patch(
            "app.api.routes.insights.get_insight_repository", return_value=mock_repo
        ):
            client = create_test_client()
            response = client.get("/insights/latest")

            data = response.json()
            insights = data["insights"]

            assert "summary" in insights
            assert "key_trends" in insights
            assert "market_sentiment" in insights
            assert "confidence" in insights

    @pytest.mark.asyncio
    async def test_confidence_model_fields(self):
        mock_insight = create_mock_insight()

        mock_repo = AsyncMock(spec=InsightRepositoryBase)
        mock_repo.load_latest = AsyncMock(return_value=mock_insight)

        with patch(
            "app.api.routes.insights.get_insight_repository", return_value=mock_repo
        ):
            client = create_test_client()
            response = client.get("/insights/latest")

            data = response.json()
            confidence = data["insights"]["confidence"]

            assert "score" in confidence
            assert "label" in confidence
            assert "badge" in confidence
            assert "source_strength" in confidence
            assert "evidence_coverage" in confidence
            assert "freshness" in confidence
            assert "consensus" in confidence
            assert "sources_count" in confidence
