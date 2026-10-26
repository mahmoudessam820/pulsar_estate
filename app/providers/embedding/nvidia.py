import asyncio
import logging
from typing import List

import httpx

from app.providers.embedding.base import EmbeddingProviderBase
from app.config.settings import settings

logger = logging.getLogger(__name__)


class NvidiaEmbeddingProvider(EmbeddingProviderBase):
    def __init__(
        self,
        api_url: str = "https://integrate.api.nvidia.com/v1/embeddings",
        max_retries: int = 3,
        api_key: str | None = settings.nvidia_api_key.get_secret_value(),
    ):
        self.api_url = api_url
        self.max_retries = max_retries
        self.headers = {"Content-Type": "application/json"}
        self.headers["Authorization"] = f"Bearer {api_key}"

    async def generate_embedding(
        self, text: str, input_type: str = "passage"
    ) -> List[float]:
        # Retry loop for transient failures
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=120.0, trust_env=False) as client:
                    response = await client.post(
                        self.api_url,
                        headers=self.headers,
                        json={
                            "input": text,
                            "input_type": input_type,
                            "model": "nvidia/nemotron-3.5-embed-1b",
                            "encoding_format": "float",
                        },
                    )
                    response.raise_for_status()
                    result = response.json()

                    # 1. Extract the full embedding
                    embedding = result["data"][0]["embedding"]

                    # 2. Matryoshka Truncation: Safely slice to the target dimension
                    target_dim = settings.embedding_dimension
                    if len(embedding) > target_dim:
                        logger.warning(
                            f"⚠️ TRUNCATING EMBEDDING: {len(embedding)} -> {target_dim} dims (Matryoshka)"
                        )
                        embedding = embedding[:target_dim]

                    # 3. Prevent silent schema corruption
                    if len(embedding) != target_dim:
                        raise ValueError(
                            f"Embedding dimension mismatch: expected {target_dim}, got {len(embedding)}"
                        )

                    # Success! Return the vector
                    return embedding

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    logger.warning(
                        f"NVIDIA Rate limited (429) on Attempt {attempt + 1}/{self.max_retries}. Retrying in 4s..."
                    )
                    if attempt == self.max_retries - 1:
                        logger.error(
                            f"NVIDIA HTTP 429 after {self.max_retries} retries: {e.response.text[:200]}"
                        )
                        raise
                    await asyncio.sleep(4)
                    continue

                if e.response.status_code >= 500:
                    logger.warning(
                        f"NVIDIA Server Error ({e.response.status_code}) on Attempt {attempt + 1}/{self.max_retries}. Retrying in 3s..."
                    )
                    if attempt == self.max_retries - 1:
                        logger.error(
                            f"NVIDIA HTTP {e.response.status_code} after {self.max_retries} retries: {e.response.text[:200]}"
                        )
                        raise
                    await asyncio.sleep(3)
                    continue

                logger.error(
                    f"NVIDIA HTTP Error {e.response.status_code}: {e.response.text[:200]}"
                )
                raise

            except httpx.TimeoutException as e:
                # guarantee we see the exception type (e.g., ReadTimeout vs ConnectTimeout)
                logger.warning(
                    f"NVIDIA timeout (Attempt {attempt + 1}/{self.max_retries}). "
                    f"Exception type: {type(e).__name__}. Details: {repr(e)}. Retrying in 3s..."
                )
                if attempt == self.max_retries - 1:
                    # exc_info=True prints the full stack trace on the final failure
                    logger.error(
                        f"NVIDIA Timeout after {self.max_retries} retries."
                        f"Exception type: {type(e).__name__}. Details: {repr(e)}",
                        exc_info=True,
                    )
                    raise
                await asyncio.sleep(3)
                continue

            except (httpx.ReadError, httpx.ConnectError) as e:
                logger.warning(
                    f"NVIDIA connection dropped (Attempt {attempt + 1}/{self.max_retries}). "
                    f"Exception type: {type(e).__name__}. Details: {repr(e)}. Retrying in 2s..."
                )
                if attempt == self.max_retries - 1:
                    logger.error(
                        f"NVIDIA Connection dropped after {self.max_retries} retries. "
                        f"Exception type: {type(e).__name__}. Details: {repr(e)}",
                        exc_info=True,
                    )
                    raise
                await asyncio.sleep(2)
                continue

            except Exception as e:
                logger.exception("Unexpected error during NVIDIA API call")
                raise
