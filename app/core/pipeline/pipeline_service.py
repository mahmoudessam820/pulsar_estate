from typing import List, Dict

from app.core.pipeline.interfaces import (
    SearchProvider,
    CrawlProvider,
    AIProvider,
)
from app.data.repositories.base import InsightRepositoryBase
from app.trust.scoring import calculate_confidence
from app.trust.explainer import explain_confidence


class PipelineService:
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

    async def run(self, query: str) -> Dict:
        urls = await self.search_provider.search(query)

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

        if len(documents) > 2:
            confidence = calculate_confidence(documents, insights)
            confidence_explanation = explain_confidence(confidence)

            insights["confidence"] = confidence
            insights["confidence_explanation"] = confidence_explanation

        result = {
            "query": query,
            "documents_collected": len(documents),
            "insights": insights,
            "sources": [d["url"] for d in documents],
        }

        await self.insight_repository.save(result)

        return result

    async def close(self):
        if hasattr(self.crawl_provider, "close"):
            await self.crawl_provider.close()
