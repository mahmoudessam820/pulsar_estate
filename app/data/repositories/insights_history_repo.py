import json
from pathlib import Path
from typing import List

from app.data.repositories.base import InsightsHistoryRepositoryBase
from app.api.schemas import InsightsHistoryItem


class InsightsHistoryRepository(InsightsHistoryRepositoryBase):
    def __init__(self, base_path: str = "storage/insights_history"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    async def save_history(self, data: InsightsHistoryItem) -> None:
        file_path = self.base_path / f"{data['id']}.json"
        file_path.write_text(json.dumps(data, indent=2))

    async def load_history(self, limit: int) -> List[InsightsHistoryItem]:
        history = []

        if not any(self.base_path.glob("*.json")):
            return []

        for file_path in self.base_path.glob("*.json"):
            with open(file_path, "r") as f:
                data = json.load(f)
                history.append(InsightsHistoryItem(**data))

        return history[-limit:]
