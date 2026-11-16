import re
import asyncio
import logging

import httpx

from app.providers.ai.base import BaseLLMProvider
from app.config.settings import settings

logger = logging.getLogger(__name__)


class GroqProvider(BaseLLMProvider):
    def __init__(self):
        super().__init__(
            provider_name="Groq",
            model=settings.groq_model,
            temperature=0.2,
            max_concurrency=1,  # Strictly sequential to respect free-tier limits
        )
        self.api_key = settings.groq_api_key.get_secret_value()

    async def _call_llm_api(self, prompt: str) -> str:
        max_retries = 5  # Increased to 5 to handle strict OTPM limits
        for attempt in range(max_retries):
            try:
                timeout = httpx.Timeout(60.0, connect=10.0)
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                }

                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.post(
                        "https://api.groq.com/openai/v1/chat/completions",
                        headers=headers,
                        json={
                            "model": self.model,
                            "temperature": self.temperature,
                            "max_tokens": 1000,  # Prevent runaway token generation
                            "messages": [{"role": "user", "content": prompt}],
                        },
                    )
                    response.raise_for_status()
                    return response.json()["choices"][0]["message"]["content"]

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    # Parse Groq's specific suggested wait time (e.g., "try again in 6.84s")
                    wait_time = 10.0  # Default fallback
                    match = re.search(r"try again in ([\d.]+)s", e.response.text)
                    if match:
                        wait_time = float(match.group(1)) + 1.0  # Add 1s buffer

                    # Use the greater of Groq's suggested time or exponential backoff
                    backoff = max(wait_time, 5 * (2**attempt))

                    logger.warning(
                        f"Groq Rate limited (429) on Attempt {attempt + 1}/{max_retries}. Retrying in {backoff:.1f}s..."
                    )
                    if attempt == max_retries - 1:
                        raise RuntimeError(f"HTTP 429 after {max_retries} retries")
                    await asyncio.sleep(backoff)
                    continue

                logger.error(
                    "Groq API error | status=%d | %s",
                    e.response.status_code,
                    e.response.text[:200],
                )
                raise RuntimeError(
                    f"HTTP {e.response.status_code}: {e.response.text[:200]}"
                )

            except httpx.TimeoutException as e:
                logger.warning(
                    f"Groq timeout (Attempt {attempt + 1}/{max_retries}). Retrying in 3s..."
                )
                if attempt == max_retries - 1:
                    raise RuntimeError(f"Timeout after {max_retries} retries: {str(e)}")
                await asyncio.sleep(3)
                continue

            except (httpx.ReadError, httpx.ConnectError) as e:
                logger.warning(
                    f"Groq connection dropped (Attempt {attempt + 1}/{max_retries}). Retrying in 2s..."
                )
                if attempt == max_retries - 1:
                    raise RuntimeError(
                        f"Connection dropped after {max_retries} retries: {str(e)}"
                    )
                await asyncio.sleep(2)
                continue

            except Exception as e:
                logger.exception("Unexpected error during Groq API call")
                raise RuntimeError(str(e))
