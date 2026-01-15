import json
from pathlib import Path
from typing import Dict, Optional

from app.data.repositories.base import InsightRepositoryBase


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
