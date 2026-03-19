from app.core.pipeline.factory import build_pipeline


async def run_daily_pipeline():
    pipeline = build_pipeline()
    try:
        await pipeline.run(
            "Dubai Luxury Residential Real Estate Market Size And Trends Analysis"
        )
    finally:
        await pipeline.close()
