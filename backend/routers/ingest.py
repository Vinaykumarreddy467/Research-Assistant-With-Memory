from fastapi import APIRouter
from models.schemas import IngestRequest, IngestResponse
from core.chunking import chunk_text
from core.retrieval import upsert_chunks

router = APIRouter()


@router.post("/ingest", response_model=IngestResponse)
async def ingest(req: IngestRequest):
    """Receive scraped text from n8n, chunk it, embed, and store in ChromaDB."""
    chunks = chunk_text(req.raw_text)
    count = upsert_chunks(url=req.url, chunks=chunks, title=req.title)
    return IngestResponse(status="success", chunks_added=count, url=req.url)
