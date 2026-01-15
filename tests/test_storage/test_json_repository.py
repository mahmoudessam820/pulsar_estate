import pytest

from app.data.repositories.insight_repo import JSONInsightRepository


@pytest.mark.asyncio
async def test_save_and_load(tmp_path):
    repo = JSONInsightRepository(base_path=tmp_path)
    data = {"test": "value"}

    await repo.save(data)
    loaded = await repo.load_latest()

    assert loaded == data
