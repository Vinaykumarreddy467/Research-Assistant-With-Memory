import os
import hashlib
import chromadb
from datetime import datetime, timezone

from .embeddings import embed_texts

PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_data")
COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "sources")

client = chromadb.PersistentClient(path=PERSIST_DIR)
collection = client.get_or_create_collection(name=COLLECTION_NAME)


def upsert_chunks(url: str, chunks: list[str], title: str = "") -> int:
    """Embed and upsert chunks into ChromaDB. Returns chunk count."""
    if not chunks:
        return 0

    embeddings = embed_texts(chunks)
    ids = []
    metadatas = []

    # Compute hash once outside the loop
    url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
    now = datetime.now(timezone.utc).isoformat()

    for i, chunk in enumerate(chunks):
        chunk_id = f"{url_hash}_{i}"
        ids.append(chunk_id)
        metadatas.append(
            {
                "source_url": url,
                "chunk_index": i,
                "title": title,
                "ingested_at": now,
            }
        )

    collection.upsert(
        ids=ids,
        documents=chunks,
        embeddings=embeddings,
        metadatas=metadatas,
    )
    return len(chunks)


def query_chunks(question_embedding: list[float], top_k: int = 5) -> dict:
    """Query ChromaDB for the most relevant chunks."""
    if collection.count() == 0:
        return {"documents": [[]], "metadatas": [[]], "distances": [[]]}

    # Don't request more results than exist
    actual_top_k = min(top_k, collection.count())

    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=actual_top_k,
        include=["documents", "metadatas", "distances"],
    )
    return results


def get_all_sources() -> list[dict]:
    """Get all unique sources with their metadata."""
    all_data = collection.get(include=["metadatas"])
    if not all_data["metadatas"]:
        return []

    sources = {}
    for meta in all_data["metadatas"]:
        url = meta["source_url"]
        if url not in sources:
            sources[url] = {
                "url": url,
                "ingested_at": meta["ingested_at"],
                "chunk_count": 0,
            }
        sources[url]["chunk_count"] += 1

    return list(sources.values())
