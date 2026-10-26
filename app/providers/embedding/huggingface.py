import asyncio
import logging
from typing import List

import httpx

from app.config.settings import settings
from app.providers.embedding.base import EmbeddingProviderBase

logger = logging.getLogger(__name__)


class HuggingFaceEmbeddingProvider(EmbeddingProviderBase):
    def __init__(
        self, 
        api_url: str = "https://router.huggingface.co/hf-inference/models/sentence-transformers/all-MiniLM-L6-v2",
        max_retries: int = 3,
        api_key: str = settings.hf_api_key.get_secret_value()
    ):
        self.api_url = api_url
        self.max_retries = max_retries
        self.headers = {"Content-Type": "application/json"}
        self.headers["Authorization"] = f"Bearer {api_key}"

    async def generate_embedding(self, text: str) -> List[float]:
        logger.info(f"STARTING embedding generation for text length: {len(text)}")
        
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=120.0, trust_env=False) as client:
                    logger.info(f"Sending request to Hugging Face API: {self.api_url}")
                    response = await client.post(
                        self.api_url, headers=self.headers, json={"inputs": text}
                    )
                    response.raise_for_status()
                    result = response.json()

                    if (
                        isinstance(result, list)
                        and len(result) > 0
                        and isinstance(result[0], list)
                    ):
                        logger.info("SUCCESS: Embedding generated successfully.")
                        return result[0]

                    logger.info("SUCCESS: Embedding generated successfully.")
                    return result

            except httpx.HTTPStatusError as e:
                # Specifically handle 429 Rate Limits with backoff
                if e.response.status_code == 429:
                    logger.warning(
                        f"Hugging Face Rate limited (429) on Attempt {attempt + 1}/{self.max_retries}. Retrying in 4s..."
                    )
                    if attempt == self.max_retries - 1:
                        logger.error(f"Hugging Face HTTP 429 after {self.max_retries} retries: {e.response.text[:200]}")
                        raise
                    await asyncio.sleep(4)
                    continue

                # Handle 5xx Server Errors (e.g., 502, 503, 504) with retry
                if e.response.status_code >= 500:
                    logger.warning(
                        f"Hugging Face Server Error ({e.response.status_code}) on Attempt {attempt + 1}/{self.max_retries}. Retrying in 3s..."
                    )
                    if attempt == self.max_retries - 1:
                        logger.error(f"Hugging Face HTTP {e.response.status_code} after {self.max_retries} retries: {e.response.text[:200]}")
                        raise
                    await asyncio.sleep(3)
                    continue

                # 4xx errors (except 429) are client errors (e.g., 400, 401, 404). Fail immediately.
                logger.error(f"Hugging Face HTTP Error {e.response.status_code}: {e.response.text[:200]}")
                raise

            except httpx.TimeoutException as e:
                # Use repr(e) to guarantee we see the exception type (e.g., ReadTimeout vs ConnectTimeout)
                logger.warning(
                    f"Hugging Face timeout (Attempt {attempt + 1}/{self.max_retries}). "
                    f"Exception type: {type(e).__name__}. Details: {repr(e)}. Retrying in 3s..."
                )
                if attempt == self.max_retries - 1:
                    # exc_info=True prints the full stack trace on the final failure
                    logger.error(
                        f"Hugging Face Timeout after {self.max_retries} retries. "
                        f"Exception type: {type(e).__name__}. Details: {repr(e)}",
                        exc_info=True
                    )
                    raise
                await asyncio.sleep(3)
                continue

            except (httpx.ReadError, httpx.ConnectError) as e:
                logger.warning(
                    f"Hugging Face connection dropped (Attempt {attempt + 1}/{self.max_retries}). "
                    f"Exception type: {type(e).__name__}. Details: {repr(e)}. Retrying in 2s..."
                )
                if attempt == self.max_retries - 1:
                    logger.error(
                        f"Hugging Face Connection dropped after {self.max_retries} retries. "
                        f"Exception type: {type(e).__name__}. Details: {repr(e)}",
                        exc_info=True
                    )
                    raise
                await asyncio.sleep(2)
                continue

            except Exception as e:
                # Unexpected errors (e.g., JSON parsing failures, bugs) should fail immediately 
                # to avoid masking programming errors with retries.
                logger.exception("Unexpected error during Hugging Face API call")
                raise
