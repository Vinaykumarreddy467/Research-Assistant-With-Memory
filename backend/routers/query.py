import os
from fastapi import APIRouter
from models.schemas import QueryRequest, QueryResponse, Citation
from core.embeddings import embed_query
from core.retrieval import query_chunks
from core.generation import generate_answer

router = APIRouter()

SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.35"))


@router.post("/query", response_model=QueryResponse)
async def query(req: QueryRequest):
    """Embed the question, retrieve top-k chunks, generate a grounded answer."""
    question_embedding = embed_query(req.question)
    results = query_chunks(question_embedding, top_k=req.top_k)

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    # Filter by similarity threshold (ChromaDB returns L2 distances; lower = more similar)
    # Convert L2 distance to cosine similarity: similarity = 1 - (distance / 2)
    filtered_chunks = []
    filtered_sources = []

    for doc, meta, dist in zip(documents, metadatas, distances):
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

    result = generate_answer(req.question, filtered_chunks, filtered_sources)
    return QueryResponse(
        answer=result["answer"],
        citations=[Citation(**c) for c in result["citations"]],
        found_in_sources=result["found_in_sources"],
    )
