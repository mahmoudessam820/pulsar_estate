# app/providers/ai/ollama.py
import logging
import asyncio
import httpx

from app.providers.ai.base import BaseLLMProvider
from app.config.settings import settings

logger = logging.getLogger(__name__)

class OllamaProvider(BaseLLMProvider):
    def __init__(self):
        super().__init__(
            provider_name="Ollama",
            model=settings.ollama_model,
            temperature=0.2,
            # Note:
            # Local LLMs are significantly slower than cloud APIs, and running them with high concurrency often causes VRAM thrashing, 
            # which dramatically slows down generation times.
            # Reducing the concurrency to 1 or 2 will actually make the overall pipeline faster and more stable by preventing your GPU/CPU from swapping memory.
            # If you switch to a cloud provider like OpenAI or NVIDIA via your .env file, 
            # you can safely revert max_concurrency back to 3 or 5 and reduce the task_time_limit back to 600, as cloud APIs are much faster.
            max_concurrency=1
        )
        self.base_url = settings.ollama_base_url
        self.api_key = settings.ollama_api_key.get_secret_value()

    async def _call_llm_api(self, prompt: str) -> str:
        max_retries = 3
        for attempt in range(max_retries):
            try:
                timeout = httpx.Timeout(180.0, connect=10.0)
                headers = {"Content-Type": "application/json"}
                if self.api_key:
                    headers["Authorization"] = f"Bearer {self.api_key}"

                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.post(
                        f"{self.base_url}/v1/chat/completions",
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

                logger.error("Ollama API error | status=%d | %s", e.response.status_code, e.response.text[:200])
                raise RuntimeError(f"HTTP {e.response.status_code}: {e.response.text[:200]}")

            except httpx.TimeoutException as e:
                logger.warning(f"Ollama timeout (Attempt {attempt + 1}/{max_retries}). Retrying in 3s...")
                if attempt == max_retries - 1:
                    raise RuntimeError(f"Timeout after {max_retries} retries: {str(e)}")
                await asyncio.sleep(3)
                continue

            except (httpx.ReadError, httpx.ConnectError) as e:
                logger.warning(f"Ollama connection dropped (Attempt {attempt + 1}/{max_retries}). Retrying in 2s...")
                if attempt == max_retries - 1:
                    raise RuntimeError(f"Connection dropped after {max_retries} retries: {str(e)}")
                await asyncio.sleep(2)
                continue

            except Exception as e:
                logger.exception("Unexpected error during Ollama API call")
                raise RuntimeError(str(e))