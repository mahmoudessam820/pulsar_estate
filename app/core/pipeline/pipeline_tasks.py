import logging

from app.core.database import AsyncSessionLocal
from app.core.pipeline.factory import build_pipeline


logger = logging.getLogger(__name__)


async def run_daily_pipeline():
    """
    Background task executed by APScheduler to run the daily intelligence pipeline.
    """
    logger.info("Starting daily pipeline execution...")

    async with AsyncSessionLocal() as db:
        try:
            pipeline = build_pipeline(db=db)

            await pipeline.run(
                "UAE Luxury Residential Real Estate Market Size and Share Report 2024-2029"
            )

            logger.info("Daily pipeline execution completed successfully.")
        except Exception as e:
            logger.error(f"Daily pipeline execution failed: {str(e)}", exc_info=True)
            raise
        finally:
            await pipeline.close()
