import json
from pathlib import Path
from typing import List

from app.data.repositories.base import InsightsHistoryRepositoryBase
from app.data.models.insights_history import InsightsHistory
from app.api.models.insights_history import InsightsHistoryResponse


class InsightsHistoryRepository(InsightsHistoryRepositoryBase):
    def __init__(self, base_path: str = "storage/insights_history"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    async def save_history(self, data: InsightsHistory) -> None:
        file_path = self.base_path / f"{data['id']}.json"
        file_path.write_text(json.dumps(data, indent=2))

    async def load_history(self, limit: int) -> List[InsightsHistoryResponse]:
        history = []

        if not any(self.base_path.glob("*.json")):
            return []

        for file_path in self.base_path.glob("*.json"):
            with open(file_path, "r") as f:
                data = json.load(f)
                history.append(InsightsHistoryResponse(**data))

        return history[-limit:]
