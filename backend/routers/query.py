import os
import logging
from fastapi import APIRouter, HTTPException
from models.schemas import QueryRequest, QueryResponse, Citation
from core.embeddings import embed_query
from core.retrieval import query_chunks
from core.generation import generate_answer
from core import db
from core.providers import LANGSMITH_ENABLED

router = APIRouter()
logger = logging.getLogger(__name__)

SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.35"))

# LangSmith traceable for the full RAG pipeline
if LANGSMITH_ENABLED:
    try:
        from langsmith import traceable

        @traceable(name="rag_query", run_type="chain")
        def _rag_pipeline(question: str, chunks: list, sources: list, history: list = None):
            """Traced RAG pipeline: generate answer from chunks."""
            return generate_answer(question, chunks, sources, history=history)
    except ImportError:
        def _rag_pipeline(question: str, chunks: list, sources: list, history: list = None):
            return generate_answer(question, chunks, sources, history=history)
else:
    def _rag_pipeline(question: str, chunks: list, sources: list, history: list = None):
        return generate_answer(question, chunks, sources, history=history)


@router.post("/query", response_model=QueryResponse)
async def query(req: QueryRequest):
    """Embed the question, retrieve top-k chunks, generate a grounded answer."""
    session = None
    where = None
    history = None

    if req.session_id:
        session = db.get_session(req.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        if session.get("source_url"):
            where = {"source_url": session["source_url"]}
        history = db.get_session_messages(req.session_id)

    # Embed the question
    try:
        question_embedding = embed_query(req.question)
    except Exception as e:
        logger.error(f"Embedding failed: {e}")
        raise HTTPException(status_code=503, detail=f"Embedding service unavailable: {e}")

    results = query_chunks(question_embedding, top_k=req.top_k, where=where)

    documents = results.get("documents", [[]])
    metadatas = results.get("metadatas", [[]])
    distances = results.get("distances", [[]])

    # Safely extract first batch (handle empty results)
    docs = documents[0] if documents and documents[0] else []
    metas = metadatas[0] if metadatas and metadatas[0] else []
    dists = distances[0] if distances and distances[0] else []

    if not docs:
        answer = "The provided sources do not contain enough information to answer this question."
        citations = []
        found_in_sources = False
        provider = None
        if req.session_id:
            db.add_message(req.session_id, "user", req.question)
            db.add_message(req.session_id, "assistant", answer, citations)
        return QueryResponse(
            answer=answer,
            citations=[],
            found_in_sources=False,
            provider=provider,
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
        answer = "The provided sources do not contain enough information to answer this question."
        citations = []
        found_in_sources = False
        provider = None
        if req.session_id:
            db.add_message(req.session_id, "user", req.question)
            db.add_message(req.session_id, "assistant", answer, citations)
        return QueryResponse(
            answer=answer,
            citations=[],
            found_in_sources=False,
            provider=provider,
        )

    # Generate answer
    try:
        history_formatted = [{"role": m["role"], "content": m["content"]} for m in history] if history else None
        result = _rag_pipeline(req.question, filtered_chunks, filtered_sources, history=history_formatted)
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        raise HTTPException(status_code=503, detail=f"LLM service unavailable: {e}")

    if req.session_id:
        db.add_message(req.session_id, "user", req.question)
        db.add_message(req.session_id, "assistant", result["answer"], result["citations"])

    return QueryResponse(
        answer=result["answer"],
        citations=[Citation(**c) for c in result["citations"]],
        found_in_sources=result["found_in_sources"],
        provider=result.get("provider"),
    )
