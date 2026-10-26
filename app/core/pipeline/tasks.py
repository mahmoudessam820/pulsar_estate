import asyncio
import logging
from datetime import datetime, timezone, timedelta

from celery import shared_task

from app.core.database import AsyncSessionLocal, engine
from app.core.pipeline.factory import build_pipeline, get_embedding_provider
from app.data.repositories.pipeline_run_repo import PostgresPipelineRunRepository
from app.data.repositories.usage_tracking_repo import PostgresUsageRepository
from app.data.repositories.user_repo import PostgresUserRepository
from app.data.repositories.insight_repo import PostgresInsightRepository
from app.events.publisher import publish_task_update
from app.monetization.limits import PLAN_LIMITS
from app.monetization.plans import Plan
from app.utils.redis_lock import (
    acquire_lock_sync,
    release_lock_sync,
    GLOBAL_PIPELINE_LOCK_KEY,
)

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    name="app.core.pipeline.tasks.execute_pipeline_task",
    autoretry_for=(Exception,),
    retry_backoff=30,
    retry_kwargs={"max_retries": 10},
)
def execute_pipeline_task(
    self,
    query: str,
    user_id: str,
    pipeline_run_id: str,
    query_embedding: list[float] | None = None,
):
    """Celery task to execute the pipeline asynchronously."""

    # 1. Sync lock check (100% safe in Celery)
    if not acquire_lock_sync(GLOBAL_PIPELINE_LOCK_KEY, ttl=600):
        logger.info(
            f"Global pipeline lock held. Retrying task {self.request.id} in 30s."
        )
        raise Exception("Global pipeline lock held, retrying...")

    try:
        # 2. asyncio.run() safely creates, runs, and destroys the loop
        asyncio.run(_run_async(query, user_id, pipeline_run_id, query_embedding))
    except Exception as e:
        """
        bind=True → the task receives self (the task instance), so it can call self.retry(...).
        Automatic retry on any Exception, with exponential-ish backoff starting at 30 s, up to 10 retries.
        """
        if "Global pipeline lock held" in str(e):
            raise self.retry(exc=e)
        logger.error(f"Task {self.request.id} failed: {str(e)}")
        raise
    finally:
        # 3. guarantee the lock is released
        release_lock_sync(GLOBAL_PIPELINE_LOCK_KEY)


async def _run_async(
    query: str,
    user_id: str,
    pipeline_run_id: str,
    query_embedding: list[float] | None = None,
):
    """The actual async pipeline execution logic."""

    pipeline = None

    async with AsyncSessionLocal() as db:
        pipeline_run_repo = PostgresPipelineRunRepository(db)
        usage_repo = PostgresUsageRepository(db)
        user_repo = PostgresUserRepository(db)
        insight_repo = PostgresInsightRepository(db)

        try:
            # EXECUTION-TIME QUOTA RE-CHECK (Safety Net)
            user = await user_repo.get_by_id(user_id)
            if not user:
                raise RuntimeError("User not found")

            plan = Plan(user.plan)
            limit = PLAN_LIMITS[plan]["daily_runs"]
            used = await usage_repo.count_today(user_id, metric_type="on_demand_run")

            if used >= limit:
                logger.warning(
                    f"Quota exceeded at execution time for user {user_id}. "
                    f"Plan: {plan.value}, Limit: {limit}, Used: {used}. Aborting task."
                )

                await pipeline_run_repo.update_run_status(
                    run_id=pipeline_run_id,
                    status="failed",
                    error="Daily quota exceeded at execution time.",
                )

                # trigger notification for quota exceeded
                publish_task_update(
                    user_id=user_id,
                    task_id=pipeline_run_id,
                    status="failed",
                    error="Daily quota exceeded.",
                )

                return  # Exit early

            # Proceed with Pipeline Execution
            logger.info(f"Starting async pipeline for user {user_id}: {query}")

            pipeline = build_pipeline(db=db)

            pipeline_result = await pipeline.run(query, user_id=user_id)

            if "error" in pipeline_result:
                raise RuntimeError(pipeline_result["error"])

            insight_id_str = pipeline_result.get("insight_id")
            start_time = pipeline_result.get("start_time", datetime.now(timezone.utc))
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()

            # Update the pipeline run record with success status and insight_id
            # We do this before populating the semantic cache to ensure that caching will be enabled only
            # when the user runs the same query again.
            await pipeline_run_repo.update_run_status(
                run_id=pipeline_run_id,
                insight_id=insight_id_str,
                status="success",
                duration_seconds=duration,
                is_cached=False,
            )

            await usage_repo.increment(str(user_id), metric_type="on_demand_run")
            logger.info(f"Successfully completed async pipeline {pipeline_run_id}")

            # Populate the semantic cache for future queries
            try:
                # Use provided embedding or generate new one
                if query_embedding is None:
                    logger.info(
                        "No embedding supplied by API; generating once in worker."
                    )
                    embedding_provider = get_embedding_provider()
                    query_embedding = await embedding_provider.generate_embedding(query)

                await insight_repo.update_cache_metadata(
                    insight_id=insight_id_str,
                    query_embedding=query_embedding,
                    cache_expires_at=datetime.now(timezone.utc) + timedelta(days=7),
                )
                logger.info(f"Successfully cached insight {insight_id_str} for 7 days")
            except Exception as e:
                logger.warning(
                    f"Failed to populate semantic cache for insight {insight_id_str}: {e}"
                )

            # trigger notification for success
            publish_task_update(
                user_id=user_id,
                task_id=pipeline_run_id,
                status="success",
                insight_id=insight_id_str,
            )

        except Exception as e:
            await pipeline_run_repo.update_run_status(
                run_id=pipeline_run_id,
                status="failed",
                error=str(e),
            )
            logger.error(
                f"Async pipeline {pipeline_run_id} failed: {str(e)}", exc_info=True
            )

            # trigger notification for failure
            publish_task_update(
                user_id=user_id,
                task_id=pipeline_run_id,
                status="failed",
                error="Pipeline execution failed. Please try again.",
            )

            raise

        finally:
            # Ensure pipeline resources are always cleaned up
            if pipeline and hasattr(pipeline, "close"):
                await pipeline.close()

            # Dispose of the SQLAlchemy engine to close all asyncpg connections.
            # This prevents the "attached to a different loop" error on the next task.
            # This is critical to avoid the classic “Future attached to a different loop” error on the next task.
            await engine.dispose()
