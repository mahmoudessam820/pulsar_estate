import uuid
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.data.models.insights import Insight
from app.data.repositories.base import InsightRepositoryBase


logger = logging.getLogger(__name__)


class PostgresInsightRepository(InsightRepositoryBase):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def save(self, data: Dict[str, Any]) -> Insight:
        """
        Saves insight data to Insight table.
        Extracts key fields for relational querying, and stores the full AI output in JSONB.
        Returns the created Insight object.
        """

        # Check if the AI provider returned an error instead of valid data
        if "error" in data and data.get("raw") is None:
            logger.error(
                "Skipping database save: AI analysis failed with error: %s",
                data.get("error"),
            )
            raise ValueError("AI analysis failed, no data to save")

        # Extract the nested 'insights' object first
        insights_obj = data.get("insights", {})

        # Check for 'summary' inside the 'insights' object
        summary = insights_obj.get("summary")
        if not summary:
            logger.warning(
                "Skipping database save: Missing required 'summary' field in 'insights' object. "
                "AI analysis likely failed, timed out, or returned empty data."
            )
            raise ValueError("Missing required 'summary' field in AI output")

        try:
            # Extract confidence from the nested 'insights' object
            confidence_obj = insights_obj.get("confidence", {})

            # Safely convert string user_id to UUID, or None if missing/global
            user_id_str = data.get("user_id")
            user_uuid = uuid.UUID(user_id_str) if user_id_str else None

            # Create a new Insights record
            new_insight = Insight(
                user_id=user_uuid,
                query=data.get("query"),
                documents_collected=data.get("documents_collected", 0),
                summary=summary,
                confidence_score=confidence_obj.get("score"),
                confidence_label=confidence_obj.get("label"),
                confidence_explanation=insights_obj.get("confidence_explanation"),
                raw_ai_output=insights_obj,
                sources=data.get("sources", []),
            )

            # Add the new record to the session and commit
            self.db.add(new_insight)
            await self.db.commit()
            await self.db.refresh(new_insight)

            logger.info(
                f"Successfully saved insight with ID: {new_insight.id} for query: {new_insight.query}"
            )

            # Return the created insight
            return new_insight

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to save insight to database: {str(e)}", exc_info=True)
            raise

    async def load_latest(self) -> Insight:
        """Load the most recently created insight from db."""
        try:
            result = await self.db.execute(
                select(Insight).order_by(Insight.created_at.desc()).limit(1)
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

    async def load_latest_for_user(self, user_id: uuid.UUID) -> Optional[Insight]:
        """Load the most recently created insight for a specific user."""
        try:
            result = await self.db.execute(
                select(Insight)
                .where(Insight.user_id == user_id)
                .order_by(Insight.created_at.desc())
                .limit(1)
            )
            insight = result.scalar_one_or_none()
            if insight:
                logger.debug(f"Loaded latest insight {insight.id} for user {user_id}")
            else:
                logger.debug(f"No insights found for user {user_id}")
            return insight
        except Exception as e:
            logger.error(
                f"Failed to load latest insight for user {user_id}: {str(e)}",
                exc_info=True,
            )
            raise

    async def find_cached_insight(
        self,
        user_id: uuid.UUID,
        query_embedding: List[float],
        max_distance: float = 0.05,
    ) -> Optional[Insight]:
        """Find a cached insight for the user within the similarity threshold."""
        try:
            # Cosine distance <=> in pgvector.
            # Distance <= 0.05 means Similarity >= 0.95
            stmt = (
                select(Insight)
                .where(
                    Insight.user_id == user_id,
                    Insight.cache_expires_at > func.now(),
                    Insight.query_embedding.isnot(None),
                    # Filter directly in the database
                    Insight.query_embedding.cosine_distance(query_embedding)
                    <= max_distance,
                )
                .order_by(Insight.query_embedding.cosine_distance(query_embedding))
                .limit(1)
            )

            result = await self.db.execute(stmt)
            cached_insight = result.scalar_one_or_none()

            if cached_insight:
                logger.info(f"Cache HIT for user {user_id}")
                return cached_insight

            return None

        except Exception as e:
            logger.error(f"Failed to find cached insight: {str(e)}", exc_info=True)
            return None

    async def find_exact_cached_insight(
        self,
        user_id: uuid.UUID,
        query: str,
    ) -> Optional[Insight]:
        """Fallback cache check: exact query match with valid embedding and expiration."""
        try:
            stmt = (
                select(Insight)
                .where(
                    Insight.user_id == user_id,
                    Insight.query == query,
                    Insight.query_embedding.isnot(None),
                    Insight.cache_expires_at > func.now(),
                )
                .order_by(Insight.created_at.desc())
                .limit(1)
            )
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(
                f"Failed to find exact cached insight: {str(e)}", exc_info=True
            )
            return None

    async def update_cache_metadata(
        self, insight_id: str, query_embedding: List[float], cache_expires_at: datetime
    ) -> None:
        """Updates the embedding and expiration time for a successfully generated insight."""
        try:
            stmt = (
                update(Insight)
                .where(Insight.id == uuid.UUID(insight_id))
                .values(
                    query_embedding=query_embedding, cache_expires_at=cache_expires_at
                )
            )
            await self.db.execute(stmt)
            await self.db.commit()
            logger.info(f"Successfully updated cache metadata for insight {insight_id}")
        except Exception as e:
            await self.db.rollback()
            logger.error(
                f"Failed to update cache metadata for insight {insight_id}: {str(e)}",
                exc_info=True,
            )
            raise
