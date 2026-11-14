import logging

import asyncio
import httpx

from app.providers.ai.base import BaseLLMProvider
from app.config.settings import settings

logger = logging.getLogger(__name__)

class OpenAIProvider(BaseLLMProvider):
    def __init__(self):
        super().__init__(
            provider_name="OpenAI",
            model=settings.openai_model,
            temperature=0.2,
            max_concurrency=5
        )
        self.api_key = settings.openai_api_key.get_secret_value()

    async def _call_llm_api(self, prompt: str) -> str:
        max_retries = 3
        for attempt in range(max_retries):
            try:
                timeout = httpx.Timeout(120.0, connect=10.0)
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }

                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.post(
                        "https://api.openai.com/v1/chat/completions",
                        headers=headers,
                        json={
                            "model": self.model,
                            "temperature": self.temperature,
                            "messages": [{"role": "user", "content": prompt}],
                        },
                    )
                    response.raise_for_status()
                    return response.json()["choices"][0]["message"]["content"]

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    logger.warning(f"Rate limited (429) on Attempt {attempt + 1}/{max_retries}. Retrying in 4s...")
                    if attempt == max_retries - 1:
                        raise RuntimeError(f"HTTP 429 after {max_retries} retries")
                    await asyncio.sleep(4)
                    continue

                logger.error("OpenAI API error | status=%d | %s", e.response.status_code, e.response.text[:200])
                raise RuntimeError(f"HTTP {e.response.status_code}: {e.response.text[:200]}")

            except httpx.TimeoutException as e:
                logger.warning(f"OpenAI timeout (Attempt {attempt + 1}/{max_retries}). Retrying in 3s...")
                if attempt == max_retries - 1:
                    raise RuntimeError(f"Timeout after {max_retries} retries: {str(e)}")
                await asyncio.sleep(3)
                continue

            except (httpx.ReadError, httpx.ConnectError) as e:
                logger.warning(f"OpenAI connection dropped (Attempt {attempt + 1}/{max_retries}). Retrying in 2s...")
                if attempt == max_retries - 1:
                    raise RuntimeError(f"Connection dropped after {max_retries} retries: {str(e)}")
                await asyncio.sleep(2)
                continue

            except Exception as e:
                logger.exception("Unexpected error during OpenAI API call")
                raise RuntimeError(str(e))