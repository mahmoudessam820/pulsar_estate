import asyncio

from app.core.pipeline.factory import build_pipeline


async def main() -> None:
    pipeline = build_pipeline()
    try:
        result = await pipeline.run("Dubai real estate market trends")
        print(result)
    finally:
        await pipeline.close()


if __name__ == "__main__":
    asyncio.run(main())
