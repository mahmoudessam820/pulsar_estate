import json
from pathlib import Path
from datetime import datetime

from app.data.repositories.base import UsageRepositoryBase


class JSONUsageRepository(UsageRepositoryBase):
    def __init__(self, file_path: str = "storage/user_usage/usage.json"):
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        if not self.file_path.exists():
            self.file_path.write_text(json.dumps({}))

    def _load(self):
        return json.loads(self.file_path.read_text())

    def _save(self, data):
        self.file_path.write_text(json.dumps(data, indent=2))

    def _today_key(self) -> str:
        return datetime.now().strftime("%Y-%m-%d")

    async def count_today(self, user_id: str) -> int:
        data = self._load()
        today = self._today_key()

        return data.get(user_id, {}).get(today, 0)

    async def increment(self, user_id: str) -> None:
        data = self._load()
        today = self._today_key()

        if user_id not in data:
            data[user_id] = {}

        data[user_id][today] = data[user_id].get(today, 0) + 1

        self._save(data)
