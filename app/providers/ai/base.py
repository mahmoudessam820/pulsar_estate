import json
import logging
import asyncio
from abc import ABC, abstractmethod
from typing import List, Dict

from rich.console import Console

from app.providers.ai.utils import parse_llm_json_response

logger = logging.getLogger(__name__)
console = Console()

class AIProviderBase(ABC):
    @abstractmethod
    async def analyze(self, documents: List[Dict]) -> Dict:
        """Analyze a list of documents and return the analysis results."""
        raise NotImplementedError


class BaseLLMProvider(AIProviderBase):
    """
    Concrete base class implementing the Map-Reduce strategy, concurrency limiting, 
    and robust JSON parsing. 
    Concrete providers only need to implement _call_llm_api.
    """
    def __init__(self, provider_name: str, model: str, temperature: float = 0.2, max_concurrency: int = 3):
        self.provider_name = provider_name
        self.model = model
        self.temperature = temperature
        self.semaphore = asyncio.Semaphore(max_concurrency)

    async def analyze(self, documents: List[Dict]) -> Dict:
        logger.info("Starting %s analysis | model=%s | docs=%d", self.provider_name, self.model, len(documents))
        console.print(f"[dim]→ {self.provider_name} analyze[/dim] ({len(documents)} documents)")

        # Validation & Filtering
        valid_docs = [d for d in documents if d.get("content") and len(str(d.get("content", ""))) > 1000]
        logger.info(f"Filtered down to {len(valid_docs)} valid documents for analysis.")

        if not valid_docs:
            return {"error": "No valid content found in the provided documents."}

        # Map Step: parallel structured extraction
        logger.info("Starting parallel extraction...")
        extraction_tasks = [self._extract_document_insights(doc) for doc in valid_docs]
        extracted_insights = await asyncio.gather(*extraction_tasks)

        structured_context = [
            insight for insight in extracted_insights
            if "error" not in insight and insight.get("key_claims")
        ]

        if not structured_context:
            return {"error": "AI failed to extract meaningful claims from any of the documents."}

        # Reduce Step: final synthesis
        logger.info("Starting final synthesis reduce step...")
        final_result = await self._synthesize_insights(structured_context)

        if "error" in final_result:
            logger.error(f"Reduce step failed with error: {final_result}")
            return final_result

        if "summary" not in final_result:
            logger.warning(f"Reduce step missing 'summary'. Raw AI output: {final_result.get('raw_output', 'N/A')}")
            console.print(f"[yellow]Warning: AI failed to generate required 'summary' field.[/yellow]")
            return {"error": "AI failed to generate required 'summary' field", "raw_output": final_result}

        if not isinstance(final_result.get("evidence"), list):
            logger.warning("AI output missing 'evidence' list. Trust system will score evidence_coverage as 0.0")
            final_result["evidence"] = []

        return final_result

    async def _extract_document_insights(self, doc: Dict) -> Dict:
        content = doc.get("content", "")
        if len(content) > 4000:
            content = content[:4000] + "\n\n...[content truncated for extraction focus]..."

        prompt = f"""
            Analyze this SINGLE real estate article. Extract key data points. 
            You MUST use the exact metadata provided. Return ONLY valid JSON:
            {{
                "source_url": "{doc.get('url')}",
                "key_claims": ["claim 1", "claim 2"],
                "data_points": ["e.g., 'Prices rose 15% in Q1'"],
                "sentiment": "positive|neutral|negative"
            }}
            
            Article Metadata:
            - URL: {doc.get('url')}
            - Published: {doc.get('published_at', 'Unknown')}
            
            Article Content:
            {content}
        """
        return await self._call_llm_api_with_semaphore(prompt)

    async def _synthesize_insights(self, structured_context: List[Dict]) -> Dict:

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
        return await self._call_llm_api_with_semaphore(prompt)

    async def _call_llm_api_with_semaphore(self, prompt: str) -> Dict:
        async with self.semaphore:
            logger.debug("Acquired semaphore for API call. Current concurrency: %d", 3 - self.semaphore._value)
            console.print(f"[dim]→ Calling {self.provider_name} API with concurrency limit[/dim] (Current concurrency: {3 - self.semaphore._value})")
            
            raw_content = await self._call_llm_api(prompt)
            return parse_llm_json_response(raw_content, self.provider_name)

    @abstractmethod
    async def _call_llm_api(self, prompt: str) -> str:
        """Concrete providers must implement this to return the raw string response from the LLM."""
        raise NotImplementedError
