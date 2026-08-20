"""
Provider manager: Groq (cloud) with automatic fallback to Ollama (local).

Priority:
  1. Groq — if GROQ_API_KEY is set, try Groq first
  2. Ollama — always available as local fallback

Handles:
  - Rate limits (429) → falls back to Ollama
  - Token limit exceeded → falls back to Ollama
  - Connection errors → falls back to Ollama
"""

import os
import logging
import httpx

logger = logging.getLogger(__name__)

# --- Config ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_BASE_URL = "https://api.groq.com/openai/v1"

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3.5:latest")


def get_active_provider() -> str:
    """Return which provider will be used."""
    if GROQ_API_KEY:
        return "groq"
    return "ollama"


# --- Groq ---
def _call_groq(system_prompt: str, user_message: str) -> str:
    """Call Groq API (OpenAI-compatible). Raises on failure."""
    response = httpx.post(
        f"{GROQ_BASE_URL}/chat/completions",
        headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
        json={
            "model": GROQ_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            "max_tokens": 1024,
            "temperature": 0.3,
        },
        timeout=30.0,
    )

    if response.status_code == 429:
        raise RateLimitError("Groq rate limit exceeded")
    if response.status_code == 400:
        body = response.json()
        if "token" in str(body).lower() or "length" in str(body).lower():
            raise TokenLimitError("Groq token limit exceeded")
        raise GroqError(f"Groq error: {body}")
    response.raise_for_status()

    return response.json()["choices"][0]["message"]["content"]


# --- Ollama ---
def _call_ollama(system_prompt: str, user_message: str) -> str:
    """Call Ollama local API."""
    response = httpx.post(
        f"{OLLAMA_BASE_URL}/api/chat",
        json={
            "model": OLLAMA_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            "stream": False,
        },
        timeout=300.0,
    )
    response.raise_for_status()
    return response.json()["message"]["content"]


# --- Public interface with fallback ---
class RateLimitError(Exception):
    pass


class TokenLimitError(Exception):
    pass


class GroqError(Exception):
    pass


def generate_with_fallback(system_prompt: str, user_message: str) -> tuple[str, str]:
    """
    Try Groq first (if configured), fall back to Ollama.
    Returns (answer_text, provider_used).
    """
    if GROQ_API_KEY:
        try:
            answer = _call_groq(system_prompt, user_message)
            logger.info("Response generated via Groq")
            return answer, "groq"
        except RateLimitError:
            logger.warning("Groq rate limited, falling back to Ollama")
        except TokenLimitError:
            logger.warning("Groq token limit exceeded, falling back to Ollama")
        except GroqError as e:
            logger.warning(f"Groq error: {e}, falling back to Ollama")
        except httpx.HTTPStatusError as e:
            logger.warning(f"Groq HTTP error: {e.response.status_code}, falling back to Ollama")
        except httpx.RequestError:
            logger.warning("Groq unreachable, falling back to Ollama")

    # Ollama fallback
    answer = _call_ollama(system_prompt, user_message)
    logger.info("Response generated via Ollama")
    return answer, "ollama"
