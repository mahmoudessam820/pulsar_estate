import logging

import asyncio
import httpx

from app.providers.ai.base import BaseLLMProvider
from app.config.settings import settings

logger = logging.getLogger(__name__)

class HuggingFaceProvider(BaseLLMProvider):
    def __init__(self):
        super().__init__(
            provider_name="Hugging Face",
            model=settings.hf_inference_model,
            temperature=0.2,
            max_concurrency=2
        )
        self.api_key = settings.hf_inference_api_key.get_secret_value()

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
                        f"https://api-inference.huggingface.co/models/{self.model}",
                        headers=headers,
                        json={
                            "inputs": prompt,
                            "parameters": {"return_full_text": False, "max_new_tokens": 2048}
                        },
                    )
                    response.raise_for_status()
                    
                    # HF Inference API returns a list of generated sequences
                    result = response.json()
                    if isinstance(result, list) and len(result) > 0:
                        return result[0]["generated_text"]
                    return str(result)

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    logger.warning(f"Rate limited (429) on Attempt {attempt + 1}/{max_retries}. Retrying in 4s...")
                    if attempt == max_retries - 1:
                        raise RuntimeError(f"HTTP 429 after {max_retries} retries")
                    await asyncio.sleep(4)
                    continue
                elif e.response.status_code == 503:
                    logger.warning(f"Model loading (503) on Attempt {attempt + 1}/{max_retries}. Retrying in 10s...")
                    if attempt == max_retries - 1:
                        raise RuntimeError(f"HTTP 503 (Model Loading) after {max_retries} retries")
                    await asyncio.sleep(10)
                    continue

                logger.error("Hugging Face API error | status=%d | %s", e.response.status_code, e.response.text[:200])
                raise RuntimeError(f"HTTP {e.response.status_code}: {e.response.text[:200]}")

            except httpx.TimeoutException as e:
                logger.warning(f"Hugging Face timeout (Attempt {attempt + 1}/{max_retries}). Retrying in 3s...")
                if attempt == max_retries - 1:
                    raise RuntimeError(f"Timeout after {max_retries} retries: {str(e)}")
                await asyncio.sleep(3)
                continue

            except (httpx.ReadError, httpx.ConnectError) as e:
                logger.warning(f"Hugging Face connection dropped (Attempt {attempt + 1}/{max_retries}). Retrying in 2s...")
                if attempt == max_retries - 1:
                    raise RuntimeError(f"Connection dropped after {max_retries} retries: {str(e)}")
                await asyncio.sleep(2)
                continue

            except Exception as e:
                logger.exception("Unexpected error during Hugging Face API call")
                raise RuntimeError(str(e))