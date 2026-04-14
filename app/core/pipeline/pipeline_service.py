import uuid
from datetime import datetime, timezone
from typing import List, Dict

from app.core.pipeline.interfaces import (
    SearchProvider,
    CrawlProvider,
    AIProvider,
)
from app.data.repositories.base import (
    InsightRepositoryBase,
    InsightsHistoryRepositoryBase,
)
from app.trust.scoring import calculate_confidence
from app.trust.explainer import explain_confidence


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
        insights_history_repository: InsightsHistoryRepositoryBase,
    ):
        self.search_provider = search_provider
        self.crawl_provider = crawl_provider
        self.ai_provider = ai_provider
        self.insight_repository = insight_repository
        self.insights_history_repository = insights_history_repository

    async def run(self, query: str) -> Dict:
        # Generate a unique ID for this pipeline run
        id = str(uuid.uuid4())
        # Record the start time of the pipeline run
        start_time = datetime.now(timezone.utc)

        try:
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

            # Only calculate confidence if we have enough documents
            if len(documents) >= 5:
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

            # Create an insight topic record
            insight_topic = {
                "id": str(uuid.uuid4()),
                "topic": query,
                "created_at": datetime.now(timezone.utc).strftime("%Y, %-m, %-d"),
            }

            topic_id = await self.insight_repository.create_insight_topic(insight_topic)
            latest_version = None

            try:
                latest_version = await self.insight_repository.get_latest_version(
                    topic_id["id"]
                )
            except Exception as e:
                print(f"Error retrieving latest version: {e}")
                pass

            version_number = 1
            if latest_version:
                version_number = latest_version.get("version", 0) + 1

            version_record = {
                "id": str(uuid.uuid4()),
                "topic_id": topic_id["id"],
                "version": version_number,
                "summary": insights.get("summary", ""),
                "confidence": insights.get("confidence", 0.0),
                "sources": [d["url"] for d in documents],
                "created_at": datetime.now(timezone.utc).strftime("%Y, %-m, %-d"),
            }

            await self.insight_repository.add_version(version_record)

            # Record pipeline run history
            duration = datetime.now(timezone.utc) - start_time
            insights_history = {
                "id": id,
                "query": query,
                "summary": insights.get("summary", ""),
                "confidence_score": insights.get("confidence", {}).get("score", 0.0),
                "timestamp": datetime.now(timezone.utc).strftime(
                    "%Y, %-m, %-d"
                ),  # Store only the date in the format "YYYY, M, D"
                "duration_seconds": round(
                    duration.total_seconds(), 2
                ),  # Store duration in seconds as a float
                "error": None,
            }

            await self.insights_history_repository.save_history(insights_history)

            return result

        except Exception as e:
            duration = (
                datetime.now(timezone.utc) - start_time
            )  # Calculate duration even on error
            insights_history = {
                "id": id,
                "query": query,
                "summary": None,
                "confidence_score": None,
                "timestamp": datetime.now(timezone.utc).strftime("%Y, %-m, %-d"),
                "duration_seconds": round(duration.total_seconds(), 2),
                "error": str(e),
            }

            await self.insights_history_repository.save_history(insights_history)

    async def close(self):
        if hasattr(self.crawl_provider, "close"):
            await self.crawl_provider.close()
