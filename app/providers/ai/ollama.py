import json
import logging
from typing import Dict, List

import httpx
from rich.console import Console

from app.providers.ai.base import AIProviderBase
from app.config.settings import settings


logger = logging.getLogger(__name__)
console = Console()


class OllamaCloudProvider(AIProviderBase):
    def __init__(
        self,
        model: str = "qwen3-vl:235b-instruct-cloud",
        temperature: float = 0.2,  #  Lower values (like 0.2) make the model more deterministic and factual, while higher values make it more creative and random.
    ):
        self.model = model
        self.temperature = temperature
        self.base_url = settings.ollama_base_url
        self.api_key = settings.ollama_api_key

    async def analyze(self, documents: List[Dict]) -> Dict:
        logger.info(
            "Starting Ollama analysis | model=%s | docs=%d", self.model, len(documents)
        )
        console.print(f"[dim]→ Ollama analyze[/dim] ({len(documents)} documents)")

        prompt = self._build_prompt(documents)

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                console.print(
                    f"[cyan]Calling Ollama API[/cyan] → {self.model}", style="dim"
                )

                response = await client.post(
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
                                    "You are a trust-first AI assistant for Dubai real estate insights."
                                    "Use only provided data. "
                                    "Never invent facts or sources."
                                    "Express uncertainty clearly."
                                    "Explain confidence, do not calculate it. "
                                    "Do NOT:"
                                    "- Fill gaps with general knowledge."
                                    "- Assume missing data."
                                    "- Guess numbers, prices, or dates."
                                    "If data is insufficient, say so."
                                    "Return ONLY valid JSON."
                                ),
                            },
                            {
                                "role": "user",
                                "content": prompt,
                            },
                        ],
                    },
                )

            response.raise_for_status()

            content = response.json()["choices"][0]["message"]["content"]

            result = self._parse_response(content)

            if "error" in result:
                logger.warning("Ollama returned invalid JSON | model=%s", self.model)
                console.print("[yellow]Warning: invalid JSON response[/yellow]")
            else:
                logger.info(
                    "Ollama analysis completed successfully | model=%s", self.model
                )
                console.print("[green]✓ Analysis complete[/green]")

            return result

        except httpx.HTTPStatusError as exc:
            logger.error(
                "Ollama API error | status=%d | %s",
                exc.response.status_code,
                exc.response.text[:200],
            )
            console.print(f"[red]API error {exc.response.status_code}[/red]")

            return {"error": f"HTTP {exc.response.status_code}", "raw": str(exc)}

        except Exception as exc:
            logger.exception("Unexpected error during Ollama analysis")
            console.print(f"[red]Unexpected error:[/red] {str(exc)}")

            return {"error": str(exc), "raw": None}

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
                            ],
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
