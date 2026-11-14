import re
import json
import logging

logger = logging.getLogger(__name__)

def parse_llm_json_response(content: str, provider_name: str) -> dict:
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
        logger.warning(f"AI returned invalid JSON. Provider: {provider_name}. Raw output snippet: {content[:500]}")
        return {
            "error": "Invalid JSON from AI",
            "raw_output": content,
        }
