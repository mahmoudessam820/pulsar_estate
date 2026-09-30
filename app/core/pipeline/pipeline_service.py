import logging
from typing import List, Dict, Optional

from app.core.pipeline.interfaces import (
    SearchProvider,
    CrawlProvider,
    AIProvider,
)
from app.data.repositories.base import (
    InsightRepositoryBase,
)
from app.trust.scoring import calculate_confidence
from app.trust.explainer import explain_confidence


logger = logging.getLogger(__name__)


class PipelineService:
    """
    Service class for running the insight generation pipeline.
    Orchestrates the full search → crawl → AI-analysis storage operations pipeline.
    """

    def __init__(
        self,
        search_provider: SearchProvider,
        crawl_provider: CrawlProvider,
        ai_provider: AIProvider,
        insight_repository: InsightRepositoryBase,
    ):
        self.search_provider = search_provider
        self.crawl_provider = crawl_provider
        self.ai_provider = ai_provider
        self.insight_repository = insight_repository

    async def run(self, query: str, user_id: Optional[str] = None) -> Dict:
        """
        Executes the full pipeline: search → crawl → AI analysis → store in DB.
        Returns the final insight result or an error message if any step fails.
        """
        try:
            urls = await self.search_provider.search(query)

            if len(urls) <= 7:
                logger.warning(
                    f"Not enough URLs found for this query '{query}'. Found {len(urls)} URLs."
                )

                return {
                    "error": "Not enough URLs found for this query",
                    "urls_found": len(urls),
                }

            documents: List[Dict] = []

            for url in urls:
                doc = await self.crawl_provider.crawl(url)

                if doc.get("error") or not doc.get("content"):
                    continue

                documents.append(doc)

            if not documents:
                return {
                    "error": "No valid documents collected",
                    "documents_collected": 0,
                }

            insights = await self.ai_provider.analyze(documents)

            # Only calculate confidence if we have enough documents
            if len(documents) >= 5:
                confidence = calculate_confidence(documents, insights)
                confidence_explanation = explain_confidence(confidence)

                insights["confidence"] = confidence
                insights["confidence_explanation"] = confidence_explanation

            result = {
                "query": query,
                "user_id": user_id,
                "documents_collected": len(documents),
                "insights": insights,
                "sources": [d["url"] for d in documents],
            }

            # Capture the returned Insight object
            saved_insight = await self.insight_repository.save(result)
            
            # Add the database ID to the result
            result["insight_id"] = str(saved_insight.id)

            return result

        except Exception as e:
            logger.error(f"Pipeline run failed: {str(e)}", exc_info=True)
            return {"error": str(e)}

    async def close(self):
        if hasattr(self.crawl_provider, "close"):
            await self.crawl_provider.close()
