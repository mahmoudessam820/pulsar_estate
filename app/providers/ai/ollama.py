import re
import json
import logging
import asyncio
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
        model: str = "minimax-m3:cloud", 
        temperature: float = 0.2,  # Lower values (like 0.2) make the model more deterministic and factual, while higher values make it more creative and random.
    ):
        self.model = model
        self.temperature = temperature
        self.base_url = settings.ollama_base_url
        self.api_key = settings.ollama_api_key
        # Limit concurrent API calls to 3 to avoid hitting the cloud provider's 429 rate limit.
        self.semaphore = asyncio.Semaphore(3)  

    async def analyze(self, documents: List[Dict]) -> Dict:
        logger.info(
            "Starting Ollama analysis | model=%s | docs=%d", self.model, len(documents)
        )
        console.print(f"[dim]→ Ollama analyze[/dim] ({len(documents)} documents)")

        # Validation & Filtering
        valid_docs = [
            d
            for d in documents
            if d.get("content") and len(str(d.get("content", ""))) > 1000
        ]
        logger.info(f"Filtered down to {len(valid_docs)} valid documents for analysis.")

        if not valid_docs:
            return {"error": "No valid content found in the provided documents."}

        # The map step parallel structured extraction
        logger.info("Starting parallel extraction...")
        extraction_tasks = [self._extract_document_insights(doc) for doc in valid_docs]
        extracted_insights = await asyncio.gather(*extraction_tasks)

        """
        - Filter out any extractions that failed
        - It looked at the results of all 10 parallel "Map" requests
        - It saw that for example: 8 of them were successful, but 2 contained the "error" key (the invalid JSON and the timeout)
        - It will silently discarded the 2 failed requests and passed only the 8 valid, structured extractions to the "Reduce" step.
        """
        structured_context = [
            insight
            for insight in extracted_insights
            if "error" not in insight and insight.get("key_claims")
        ]

        if not structured_context:
            return {
                "error": "AI failed to extract meaningful claims from any of the documents."
            }

        # The reduce Step final synthesis
        logger.info("Starting final synthesis reduce step...")
        final_result = await self._synthesize_insights(structured_context)

        return final_result

    async def _extract_document_insights(self, doc: Dict) -> Dict:
        """Map Step: Extract structured facts from a SINGLE document."""
        content = doc.get("content", "")
        if len(content) > 4000:
            content = (
                content[:4000] + "\n\n...[content truncated for extraction focus]..."
            )

        prompt = f"""
            Analyze this SINGLE real estate article. Extract key data points. 
            You MUST use the exact metadata provided. Return ONLY valid JSON:
            {{
                "source_url": "{doc.get("url")}",
                "key_claims": ["claim 1", "claim 2"],
                "data_points": ["e.g., 'Prices rose 15% in Q1'"],
                "sentiment": "positive|neutral|negative"
            }}
            
            Article Metadata:
            - URL: {doc.get("url")}
            - Published: {doc.get("published_at", "Unknown")}
            
            Article Content:
            {content}
        """

        # Use the semaphore-wrapped caller
        return await self._call_api_with_semaphore(prompt)

    async def _synthesize_insights(self, structured_context: List[Dict]) -> Dict:
        """Reduce Step: Synthesize the structured extractions into a final report."""
        context_str = json.dumps(structured_context, indent=2)

        prompt = f"""
            You are a trust-first AI assistant for United Arab Emirates real estate insights.
            Analyze the following structured data extracted from multiple sources.
            
            Your task:
            1. Identify overarching market trends.
            2. Detect and explicitly mention any conflicting information between sources.
            3. Generate a comprehensive, factual summary.
            
            Return ONLY valid JSON in this EXACT format. Do not add any conversational text outside the JSON:
            {{
                "summary": "A comprehensive 2-3 sentence summary of the market based on the data.",
                "key_trends": ["Trend 1", "Trend 2"],
                "market_sentiment": "positive|neutral|negative|mixed",
                "evidence": [
                    {{
                        "claim": "A specific factual claim extracted from the data",
                        "source_url": "The EXACT source_url from the structured data"
                    }}
                ]
            }}

            Structured Data from Sources:
            {context_str}
        """

        final_result = await self._call_api_with_semaphore(prompt)

        if "error" in final_result:
            logger.error(f"Reduce step failed with error: {final_result}")
            return final_result

        # Detailed debugging if the AI forgets the summary
        if "summary" not in final_result:
            logger.warning(
                f"Reduce step missing 'summary'. Raw AI output: {final_result.get('raw_output', json.dumps(final_result))}"
            )
            console.print(
                f"[yellow]Warning: AI failed to generate required 'summary' field. Raw output: {final_result.get('raw_output', 'N/A')}[/yellow]"
            )
            return {
                "error": "AI failed to generate required 'summary' field",
                "raw_output": final_result,
            }

        if not isinstance(final_result.get("evidence"), list):
            logger.warning(
                "AI output missing 'evidence' list. Trust system will score evidence_coverage as 0.0"
            )
            final_result["evidence"] = []

        return final_result

    async def _call_api_with_semaphore(self, prompt: str, max_retries: int = 3) -> Dict:
        """Wraps the API call with a semaphore to enforce concurrency limits."""
        async with self.semaphore:
            logger.debug(
                "Acquired semaphore for API call. Current concurrency: %d",
                3 - self.semaphore._value,
            )
            console.print(
                f"[dim]→ Calling Ollama API with concurrency limit[/dim] (Current concurrency: {3 - self.semaphore._value})"
            )
            return await self._call_api(prompt, max_retries)

    async def _call_api(self, prompt: str, max_retries: int = 3) -> Dict:
        """Robust API caller with retries."""
        for attempt in range(max_retries):
            try:
                timeout = httpx.Timeout(180.0, connect=10.0)
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.post(
                        f"{self.base_url}/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {self.api_key.get_secret_value()}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "model": self.model,
                            "temperature": self.temperature,
                            "messages": [{"role": "user", "content": prompt}],
                        },
                    )

                    response.raise_for_status()
                    content = response.json()["choices"][0]["message"]["content"]
                    return self._parse_response(content)
            except httpx.HTTPStatusError as e:
                # Specifically handle 429 Rate Limits with backoff
                if e.response.status_code == 429:
                    logger.warning(
                        f"Rate limited (429) on Attempt {attempt + 1}/{max_retries}. Retrying in 4s..."
                    )
                    console.print(
                        f"[yellow]Warning: Rate limited (429) on Attempt {attempt + 1}/{max_retries}. Retrying in 4s...[/yellow]"
                    )
                    if attempt == max_retries - 1:
                        return {"error": f"HTTP 429 after {max_retries} retries"}
                    await asyncio.sleep(4)
                    continue

                logger.error(
                    "Ollama API error | status=%d | %s",
                    e.response.status_code,
                    e.response.text[:200],
                )
                console.print(f"[red]API error {e.response.status_code}[/red]")
                return {
                    "error": f"HTTP {e.response.status_code}",
                    "raw_output": e.response.text[:500],
                }
            except (httpx.ReadError, httpx.ConnectError) as e:
                logger.warning(
                    f"Ollama connection dropped (Attempt {attempt + 1}/{max_retries}). Retrying in 2s..."
                )
                console.print(
                    f"[yellow]Warning: Ollama connection dropped (Attempt {attempt + 1}/{max_retries}). Retrying in 2s...[/yellow]"
                )
                if attempt == max_retries - 1:
                    return {
                        "error": f"Connection dropped after {max_retries} retries: {str(e)}"
                    }
                await asyncio.sleep(2)
            except Exception as e:
                logger.exception("Unexpected error during Ollama API call")
                console.print(f"[red]Unexpected error:[/red] {str(e)}")
                return {"error": str(e), "raw_output": None}

    def _parse_response(self, content: str) -> Dict:
        """
        Bulletproof JSON parser.
        Extracts JSON even if the AI wraps it in markdown code blocks or adds conversational text.
        """
        try:
            # 1. Try to extract from ```json ... ``` markdown blocks
            json_match = re.search(r"```json\s*(.*?)\s*```", content, re.DOTALL)
            if json_match:
                clean_content = json_match.group(1)
            else:
                # 2. Try to find raw JSON object boundaries
                start_idx = content.find("{")
                end_idx = content.rfind("}")
                if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                    clean_content = content[start_idx : end_idx + 1]
                else:
                    clean_content = content

            return json.loads(clean_content.strip())
        except json.JSONDecodeError:
            logger.warning(
                "AI returned invalid JSON. Raw output snippet: %s", content[:500]
            )
            return {
                "error": "Invalid JSON from AI",
                "raw_output": content,
            }
