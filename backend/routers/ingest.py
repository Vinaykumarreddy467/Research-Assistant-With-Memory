import logging
from fastapi import APIRouter, HTTPException
from models.schemas import IngestRequest, IngestResponse
from core.chunking import chunk_text
from core.retrieval import upsert_chunks

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/ingest", response_model=IngestResponse)
async def ingest(req: IngestRequest):
    """Receive scraped text from n8n, chunk it, embed, and store in ChromaDB."""
    chunks = chunk_text(req.raw_text)

    try:
        count = upsert_chunks(url=req.url, chunks=chunks, title=req.title)
    except Exception as e:
        logger.error(f"Embedding/storage failed for {req.url}: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Embedding service unavailable: {e}",
        )

    return IngestResponse(status="success", chunks_added=count, url=req.url)
