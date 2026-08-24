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
import re
import httpx

logger = logging.getLogger(__name__)

# --- LangSmith tracing (optional) ---
LANGSMITH_ENABLED = os.getenv("LANGSMITH_TRACING", "").lower() == "true" and bool(os.getenv("LANGSMITH_API_KEY"))
_run = None
_trace = None

if LANGSMITH_ENABLED:
    try:
        from langsmith import traceable
        from langsmith import Client as LangSmithClient

        _ls_client = LangSmithClient()
        logger.info("LangSmith tracing enabled")

        def trace_llm_call(func):
            """Decorator to trace LLM calls with LangSmith."""
            @traceable(
                name=func.__name__,
                run_type="llm",
                metadata={
                    "project": os.getenv("LANGSMITH_PROJECT", "research-assistant"),
                },
            )
            def wrapper(system_prompt: str, user_message: str, history: list[dict] = None, **kwargs):
                return func(system_prompt, user_message, history=history, **kwargs)
            return wrapper
    except ImportError:
        logger.warning("langsmith package not installed, tracing disabled")
        LANGSMITH_ENABLED = False
        def trace_llm_call(func):
            return func
else:
    def trace_llm_call(func):
        return func


# --- Custom exceptions (defined before usage) ---
class RateLimitError(Exception):
    pass


class TokenLimitError(Exception):
    pass


class GroqError(Exception):
    pass


# --- Config ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_BASE_URL = "https://api.groq.com/openai/v1"

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")


def get_active_provider() -> str:
    """Return which provider will be used."""
    if GROQ_API_KEY:
        return "groq"
    return "ollama"


# --- Groq ---
@trace_llm_call
def _call_groq(system_prompt: str, user_message: str, history: list[dict] = None) -> str:
    """Call Groq API (OpenAI-compatible). Raises on failure."""
    messages = [{"role": "system", "content": system_prompt}]
    if history:
        for msg in history:
            messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_message})

    response = httpx.post(
        f"{GROQ_BASE_URL}/chat/completions",
        headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
        json={
            "model": GROQ_MODEL,
            "messages": messages,
            "max_tokens": 4096,
            "temperature": 0.3,
        },
        timeout=30.0,
    )

    if response.status_code == 429:
        raise RateLimitError("Groq rate limit exceeded")
    if response.status_code == 400:
        try:
            body = response.json()
        except Exception:
            body = {"raw": response.text}
        if "token" in str(body).lower() or "length" in str(body).lower():
            raise TokenLimitError("Groq token limit exceeded")
        raise GroqError(f"Groq error: {body}")
    response.raise_for_status()

    return response.json()["choices"][0]["message"]["content"]


# --- Ollama ---
@trace_llm_call
def _call_ollama(system_prompt: str, user_message: str, history: list[dict] = None) -> str:
    """Call Ollama local API."""
    messages = [{"role": "system", "content": system_prompt}]
    if history:
        for msg in history:
            messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_message})

    response = httpx.post(
        f"{OLLAMA_BASE_URL}/api/chat",
        json={
            "model": OLLAMA_MODEL,
            "messages": messages,
            "stream": False,
        },
        timeout=None,
    )
    response.raise_for_status()
    return response.json()["message"]["content"]


# --- Public interface with fallback ---
def generate_with_fallback(system_prompt: str, user_message: str, history: list[dict] = None) -> tuple[str, str]:
    """
    Try Groq first (if configured), fall back to Ollama.
    Returns (answer_text, provider_used).
    """
    if GROQ_API_KEY:
        try:
            answer = _call_groq(system_prompt, user_message, history)
            logger.info("Response generated via Groq")
            # Strip reasoning process tags if present
            answer = re.sub(r"<think>.*?</think>", "", answer, flags=re.DOTALL).strip()
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
    answer = _call_ollama(system_prompt, user_message, history)
    logger.info("Response generated via Ollama")
    # Strip reasoning process tags if present
    answer = re.sub(r"<think>.*?</think>", "", answer, flags=re.DOTALL).strip()
    return answer, "ollama"
