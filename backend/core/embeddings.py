import os
import httpx

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "qwen3-embedding:8b")


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Get embeddings for a list of texts via Ollama."""
    embeddings = []
    for text in texts:
        response = httpx.post(
            f"{OLLAMA_BASE_URL}/api/embed",
            json={"model": EMBEDDING_MODEL, "input": text},
            timeout=60.0,
        )
        response.raise_for_status()
        data = response.json()
        embeddings.append(data["embeddings"][0])
    return embeddings


def embed_query(text: str) -> list[float]:
    """Get embedding for a single query string."""
    return embed_texts([text])[0]
