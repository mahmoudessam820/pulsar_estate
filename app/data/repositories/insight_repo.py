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

    async def create_insight_topic(self, topic: Dict[str, str]) -> Dict:
        file_path = self.base_path / f"topic-{topic['id']}.json"
        file_path.write_text(json.dumps(topic, indent=2))
        return topic

    async def add_version(self, version: Dict) -> None:
        file_path = self.base_path / f"version-{version['id']}.json"
        file_path.write_text(json.dumps(version, indent=2))

    async def get_latest_version(self, version_id: str) -> Optional[Dict]:
        file_path = self.base_path / f"version-{version_id}.json"
        if file_path.exists():
            return json.loads(file_path.read_text())
        return None

    async def load_topics(self, topic_id: str) -> Optional[Dict]:
        topics = []
        for file in self.base_path.glob(f"topic-{topic_id}.json"):
            topics.append(json.loads(file.read_text()))
        return topics
