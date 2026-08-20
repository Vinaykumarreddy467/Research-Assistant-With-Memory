import os
import httpx

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "qwen3-embedding:8b")


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Get embeddings for a list of texts via Ollama. Uses batching."""
    if not texts:
        return []

    response = httpx.post(
        f"{OLLAMA_BASE_URL}/api/embed",
        json={"model": EMBEDDING_MODEL, "input": texts},
        timeout=httpx.Timeout(300.0, read=300.0),
    )
    response.raise_for_status()
    data = response.json()
    return data["embeddings"]


def embed_query(text: str) -> list[float]:
    """Get embedding for a single query string."""
    return embed_texts([text])[0]
