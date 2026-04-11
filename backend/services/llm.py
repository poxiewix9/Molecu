"""LLM wrapper — uses Google Gemini. Skips gracefully if rate-limited or unavailable."""

import os
import json
import logging
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

log = logging.getLogger(__name__)

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
MODEL = "gemini-2.0-flash"

if not GOOGLE_API_KEY:
    log.warning(
        "GOOGLE_API_KEY is not set. LLM features (summaries, grant drafts) will use "
        "fallback responses. Set the key in backend/.env or as an environment variable."
    )

_client = None


def _get_client():
    global _client
    if _client is not None:
        return _client
    if not GOOGLE_API_KEY:
        log.warning("No Google API key — LLM calls will use fallback responses")
        return None
    try:
        from google import genai
        _client = genai.Client(api_key=GOOGLE_API_KEY)
        return _client
    except Exception as e:
        log.warning("Failed to init Gemini client: %s", e)
        return None


async def ask_llm(system_prompt: str, user_prompt: str, max_tokens: int = 2048) -> str:
    """Calls Gemini. Returns empty string immediately on any error — never blocks."""
    client = _get_client()
    if client is None:
        return ""
    try:
        combined = f"{system_prompt}\n\n{user_prompt}"
        response = client.models.generate_content(
            model=MODEL,
            contents=combined,
            config={"max_output_tokens": max_tokens, "temperature": 0.3},
        )
        return response.text or ""
    except Exception as e:
        log.info("Gemini unavailable (rate limit or error), using fallback: %s", str(e)[:80])
        return ""


async def ask_llm_json(system_prompt: str, user_prompt: str, max_tokens: int = 2048) -> dict | list | None:
    """Ask the LLM and parse as JSON. Returns None immediately on any error."""
    raw = await ask_llm(
        system_prompt + "\n\nRespond ONLY with valid JSON, no markdown fences.",
        user_prompt,
        max_tokens,
    )
    if not raw:
        return None
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        log.warning("LLM returned non-JSON: %s…", raw[:200])
        return None
