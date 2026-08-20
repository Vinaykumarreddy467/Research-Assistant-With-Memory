import os
import logging
from fastapi import APIRouter, HTTPException
from models.schemas import QueryRequest, QueryResponse, Citation
from core.embeddings import embed_query
from core.retrieval import query_chunks
from core.generation import generate_answer

router = APIRouter()
logger = logging.getLogger(__name__)

SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.35"))


@router.post("/query", response_model=QueryResponse)
async def query(req: QueryRequest):
    """Embed the question, retrieve top-k chunks, generate a grounded answer."""
    # Embed the question
    try:
        question_embedding = embed_query(req.question)
    except Exception as e:
        logger.error(f"Embedding failed: {e}")
        raise HTTPException(status_code=503, detail=f"Embedding service unavailable: {e}")

    results = query_chunks(question_embedding, top_k=req.top_k)

    documents = results.get("documents", [[]])
    metadatas = results.get("metadatas", [[]])
    distances = results.get("distances", [[]])

    # Safely extract first batch (handle empty results)
    docs = documents[0] if documents and documents[0] else []
    metas = metadatas[0] if metadatas and metadatas[0] else []
    dists = distances[0] if distances and distances[0] else []

    if not docs:
        return QueryResponse(
            answer="The provided sources do not contain enough information to answer this question.",
            citations=[],
            found_in_sources=False,
        )

    # Filter by similarity threshold
    filtered_chunks = []
    filtered_sources = []

    for doc, meta, dist in zip(docs, metas, dists):
        similarity = 1 - (dist / 2)
        if similarity >= SIMILARITY_THRESHOLD:
            filtered_chunks.append(doc)
            filtered_sources.append(meta["source_url"])

    if not filtered_chunks:
        return QueryResponse(
            answer="The provided sources do not contain enough information to answer this question.",
            citations=[],
            found_in_sources=False,
        )

    # Generate answer
    try:
        result = generate_answer(req.question, filtered_chunks, filtered_sources)
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        raise HTTPException(status_code=503, detail=f"LLM service unavailable: {e}")

    return QueryResponse(
        answer=result["answer"],
        citations=[Citation(**c) for c in result["citations"]],
        found_in_sources=result["found_in_sources"],
    )
