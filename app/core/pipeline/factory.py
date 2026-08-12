import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pipeline.pipeline_service import PipelineService
from app.providers.search.duckduckgo import DuckDuckGoSearchProvider
from app.providers.crawler.crawl4ai import Crawl4AIProvider
from app.providers.ai.ollama import OllamaCloudProvider
from app.data.repositories.insight_repo import PostgresInsightRepository
from app.data.repositories.insights_history_repo import InsightsHistoryRepository


logger = logging.getLogger(__name__)


def build_pipeline(db: AsyncSession) -> PipelineService:
    """
    Factory function to build and configure the PipelineService.

    Args:
        db: The async database session, injected to support the Postgres repository.

    Returns:
        A fully configured PipelineService instance.
    """
    logger.debug("Building PipelineService with PostgreSQL repository")

    # 1. Initialize Providers
    search_provider = DuckDuckGoSearchProvider()
    crawl_provider = Crawl4AIProvider()
    ai_provider = OllamaCloudProvider()

    # 2. Initialize Repositories
    insight_repository = PostgresInsightRepository(db=db)
    insights_history_repository = InsightsHistoryRepository()

    # 3. Assemble and return the Pipeline Service
    pipeline_service = PipelineService(
        search_provider=search_provider,
        crawl_provider=crawl_provider,
        ai_provider=ai_provider,
        insight_repository=insight_repository,
        insights_history_repository=insights_history_repository,
    )

    logger.info("PipelineService successfully built and configured")
    return pipeline_service
