import os
import hashlib
import chromadb
from datetime import datetime, timezone

from .embeddings import embed_texts

PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_data")
COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "sources")

client = chromadb.PersistentClient(path=PERSIST_DIR)
collection = client.get_or_create_collection(name=COLLECTION_NAME)

# Gracefully handle dimensionality mismatch
try:
    if collection.count() > 0:
        # Run a test query with a dummy embedding to verify dimensionality match
        test_emb = embed_texts(["test"])[0]
        collection.query(query_embeddings=[test_emb], n_results=1)
except Exception as e:
    err_str = str(e).lower()
    if "dimension" in err_str or "dimensionality" in err_str:
        import sys
        print(f"WARNING: Dimensionality mismatch detected for collection '{COLLECTION_NAME}' (likely due to a new embedding model). Recreating...", file=sys.stderr)
        try:
            client.delete_collection(COLLECTION_NAME)
            collection = client.get_or_create_collection(name=COLLECTION_NAME)
        except Exception as delete_err:
            print(f"Failed to reset mismatched collection: {delete_err}", file=sys.stderr)


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


def query_chunks(question_embedding: list[float], top_k: int = 5, where: dict = None) -> dict:
    """Query ChromaDB for the most relevant chunks."""
    if collection.count() == 0:
        return {"documents": [[]], "metadatas": [[]], "distances": [[]]}

    # Don't request more results than exist
    actual_top_k = min(top_k, collection.count())

    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=actual_top_k,
        where=where,
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
