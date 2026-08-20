from fastapi import APIRouter
from models.schemas import SourcesResponse, SourceItem
from core.retrieval import get_all_sources

router = APIRouter()


@router.get("/sources", response_model=SourcesResponse)
async def sources():
    """Return all ingested sources."""
    raw_sources = get_all_sources()
    items = [SourceItem(**s) for s in raw_sources]
    return SourcesResponse(sources=items)
