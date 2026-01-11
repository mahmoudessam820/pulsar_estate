import json
import httpx
from typing import Dict, List

from app.providers.ai.base import AIProviderBase
from app.config.settings import settings


class OllamaCloudProvider(AIProviderBase):
    def __init__(
        self,
        model: str = "llama3.1",
        temperature: float = 0.2,
    ):
        self.model = model
        self.temperature = temperature
        self.base_url = settings.ollama_base_url
        self.api_key = settings.ollama_api_key

    def analyze(self, documents: List[Dict]) -> Dict:
        prompt = self._build_prompt(documents)

        response = httpx.post(
            f"{self.base_url}/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "temperature": self.temperature,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are a real estate market analyst. "
                            "Return ONLY valid JSON."
                        ),
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
            },
            timeout=60,
        )

        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]

        return self._parse_response(content)

    def _build_prompt(self, documents: List[Dict]) -> str:
        sources = [
            {
                "url": d["url"],
                "title": d.get("title"),
                "published_at": d.get("published_at"),
                "content": d.get("content"),
            }
            for d in documents
            if d.get("content")
        ]

        return f"""
                    Analyze the following real estate articles and return JSON in this format:

                    {{
                        "summary": "...",
                        "key_trends": ["...", "..."],
                        "market_sentiment": "positive|neutral|negative",
                        "evidence": [
                            {{
                            "claim": "...",
                            "source_url": "..."
                            }}
                        ]
                    }}

                    Articles:
                    {sources}
                """

    def _parse_response(self, content: str) -> Dict:
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {
                "error": "Invalid JSON from AI",
                "raw_output": content,
            }
