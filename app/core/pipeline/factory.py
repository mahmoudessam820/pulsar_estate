from app.core.pipeline.pipeline_service import PipelineService
from app.providers.search.duckduckgo import DuckDuckGoSearchProvider
from app.providers.crawler.crawl4ai import Crawl4AIProvider
from app.providers.ai.ollama import OllamaCloudProvider
from app.data.repositories.insight_repo import JSONInsightRepository
from app.data.repositories.insights_history_repo import InsightsHistoryRepository


def build_pipeline() -> PipelineService:
    return PipelineService(
        search_provider=DuckDuckGoSearchProvider(),
        crawl_provider=Crawl4AIProvider(),
        ai_provider=OllamaCloudProvider(),
        insight_repository=JSONInsightRepository(),
        insights_history_repository=InsightsHistoryRepository(),
    )
