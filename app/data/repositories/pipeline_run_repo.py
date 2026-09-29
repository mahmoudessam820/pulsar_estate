import uuid
import logging
from typing import List, Optional
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.data.repositories.base import PipelineRunRepositoryBase
from app.data.models.pipeline_runs import PipelineRun

logger = logging.getLogger(__name__)


class PostgresPipelineRunRepository(PipelineRunRepositoryBase):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_run(self, user_id: Optional[str] = None) -> PipelineRun:
        """Create a new pipeline run record with status='pending'."""
        try:
            user_uuid = uuid.UUID(user_id) if user_id else None

            new_run = PipelineRun(user_id=user_uuid, status="pending")

            self.db.add(new_run)
            await self.db.commit()
            await self.db.refresh(new_run)
            logger.info(
                f"Created pipeline run {new_run.id} for user {user_id or 'system'}"
            )
            return new_run
        except ValueError:
            logger.warning(f"Invalid UUID format for user_id: {user_id}")
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to create pipeline run: {str(e)}", exc_info=True)
            raise

    async def update_run_status(
        self,
        run_id: str,
        status: str,
        insight_id: Optional[str] = None,
        error: Optional[str] = None,
        duration_seconds: Optional[float] = None,
    ) -> None:
        """Update run status, optionally with insight_id, error, or duration."""
        try:
            stmt = select(PipelineRun).where(PipelineRun.id == uuid.UUID(run_id))
            result = await self.db.execute(stmt)
            run = result.scalar_one_or_none()

            if not run:
                logger.warning(
                    f"Attempted to update non-existent pipeline run: {run_id}"
                )
                return

            run.status = status
            if insight_id:
                run.insight_id = uuid.UUID(insight_id)
            if error:
                run.error = error
            if duration_seconds is not None:
                run.duration_seconds = duration_seconds

            # Set completed_at if status is terminal
            if status in ["success", "failed"]:
                run.completed_at = datetime.now(timezone.utc)

            await self.db.commit()
            await self.db.refresh(run)
            logger.info(f"Updated pipeline run {run_id} to status: {status}")
        except ValueError as e:
            logger.warning(f"Invalid UUID format: {str(e)}")
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(
                f"Failed to update pipeline run {run_id}: {str(e)}", exc_info=True
            )
            raise

    async def get_run(self, run_id: str) -> Optional[PipelineRun]:
        """Get a specific pipeline run by ID."""
        try:
            stmt = select(PipelineRun).where(PipelineRun.id == uuid.UUID(run_id))
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
        except ValueError:
            logger.warning(f"Invalid UUID format for run_id: {run_id}")
            return None
        except Exception as e:
            logger.error(
                f"Failed to get pipeline run {run_id}: {str(e)}", exc_info=True
            )
            raise

    async def get_recent_runs(self, limit: int = 20) -> List[PipelineRun]:
        """Get recent pipeline runs, ordered by started_at DESC."""
        try:
            stmt = (
                select(PipelineRun).order_by(PipelineRun.started_at.desc()).limit(limit)
            )

            result = await self.db.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to get recent pipeline runs: {str(e)}", exc_info=True)
            raise
