import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pipeline.pipeline_service import PipelineService
from app.providers.search.duckduckgo import DuckDuckGoSearchProvider
from app.providers.crawler.crawl4ai import Crawl4AIProvider
from app.providers.ai.ollama import OllamaCloudProvider
from app.data.repositories.insight_repo import PostgresInsightRepository
from app.providers.embedding.base import EmbeddingProviderBase
from app.providers.embedding.huggingface import HuggingFaceEmbeddingProvider
from app.providers.embedding.nvidia import NvidiaEmbeddingProvider
from app.config.settings import settings


logger = logging.getLogger(__name__)


def get_embedding_provider() -> EmbeddingProviderBase:
    """
    Resolves and returns the configured EmbeddingProviderBase.
    Defaults to invalid if not specified or Hugging Face.
    """
    provider_type = settings.embedding_provider.lower()
    if provider_type == "huggingface":
        logger.info("Using Hugging Face Embedding Provider")
        return HuggingFaceEmbeddingProvider()
    else:
        logger.info("Using NVIDIA NIM Embedding Provider")
        return NvidiaEmbeddingProvider()


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

    # 3. Assemble and return the Pipeline Service
    pipeline_service = PipelineService(
        search_provider=search_provider,
        crawl_provider=crawl_provider,
        ai_provider=ai_provider,
        insight_repository=insight_repository,
    )

    logger.info("PipelineService successfully built and configured")
    return pipeline_service
