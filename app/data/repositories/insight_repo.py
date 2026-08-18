import json
import logging
from pathlib import Path
from typing import Dict, Optional, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.data.models.insights import Insights
from app.data.repositories.base import InsightRepositoryBase


logger = logging.getLogger(__name__)


class PostgresInsightRepository(InsightRepositoryBase):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def save(self, data: Dict[str, Any]) -> None:
        """
        Saves insight data to PostgreSQL.
        Extracts key fields for relational querying, and stores the full AI output in JSONB.
        """
        # Check if the AI provider returned an error instead of valid data
        if "error" in data and data.get("raw") is None:
            logger.error(
                "Skipping database save: AI analysis failed with error: %s",
                data.get("error"),
            )
            return

        # Extract the nested 'insights' object first
        insights_obj = data.get("insights", {})

        # Check for 'summary' inside the 'insights' object
        summary = insights_obj.get("summary")
        if not summary:
            logger.warning(
                "Skipping database save: Missing required 'summary' field in 'insights' object. "
                "AI analysis likely failed, timed out, or returned empty data."
            )
            return

        try:
            # Extract confidence from the nested 'insights' object
            confidence_obj = insights_obj.get("confidence", {})

            # Create a new Insights record
            new_insight = Insights(
                query=data.get("query"),
                documents_collected=data.get("documents_collected", 0),
                summary=summary,  # Use the correctly extracted summary
                confidence_score=confidence_obj.get("score"),
                confidence_label=confidence_obj.get("label"),
                confidence_explanation=insights_obj.get("confidence_explanation"),
                raw_ai_output=insights_obj,  # Store the whole nested object for API reconstruction
                sources=data.get("sources", []),
            )

            # Add the new record to the session and commit
            self.db.add(new_insight)
            await self.db.commit()
            await self.db.refresh(new_insight)
            logger.info(
                f"Successfully saved insight with ID: {new_insight.id} for query: {new_insight.query}"
            )
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to save insight to database: {str(e)}", exc_info=True)
            raise

    async def load_latest(self) -> Insights:
        """Load the most recently created insight from db."""
        try:
            result = await self.db.execute(
                select(Insights).order_by(Insights.created_at.desc()).limit(1)
            )
            insight = result.scalar_one_or_none()
            if insight:
                logger.debug(f"Loaded latest insight {insight.id}")
            else:
                logger.debug("No insights found in database")
            return insight
        except Exception as e:
            logger.error(f"Failed to load latest insight: {str(e)}", exc_info=True)
            raise

    async def create_insight_topic(self, topic: Dict[str, str]):
        raise NotImplementedError("Pending migration of InsightTopic table")

    async def add_version(self, version):
        raise NotImplementedError("Pending migration of InsightVersion table")

    async def get_latest_version(self, insight_id):
        raise NotImplementedError("Pending migration of InsightVersion table")

    async def load_topics(self, topic_id: str):
        raise NotImplementedError("Pending migration of InsightTopic table")


class JSONInsightRepository(InsightRepositoryBase):
    def __init__(self, base_path: str = "storage/insights"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    async def save(self, data: Dict) -> None:
        file_path = self.base_path / "latest.json"
        file_path.write_text(json.dumps(data, indent=2))

    async def load_latest(self) -> Optional[Dict]:
        file_base = self.base_path / "latest.json"

        if not file_base.exists():
            return None

        return json.loads(file_base.read_text())

    async def create_insight_topic(self, topic: Dict[str, str]) -> Dict:
        file_path = self.base_path / f"topic-{topic['id']}.json"
        file_path.write_text(json.dumps(topic, indent=2))
        return topic

    async def add_version(self, version: Dict) -> None:
        file_path = self.base_path / f"version-{version['id']}.json"
        file_path.write_text(json.dumps(version, indent=2))

    async def get_latest_version(self, version_id: str) -> Optional[Dict]:
        file_path = self.base_path / f"version-{version_id}.json"
        if file_path.exists():
            return json.loads(file_path.read_text())
        return None

    async def load_topics(self, topic_id: str) -> Optional[Dict]:
        topics = []
        for file in self.base_path.glob(f"topic-{topic_id}.json"):
            topics.append(json.loads(file.read_text()))
        return topics
