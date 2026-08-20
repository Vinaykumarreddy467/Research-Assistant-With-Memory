import os
import re
import hashlib
import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from core.chunking import chunk_text
from core.retrieval import upsert_chunks

router = APIRouter()


class DirectIngestRequest(BaseModel):
    url: str


def strip_html(html: str) -> str:
    """Basic HTML to text conversion."""
    text = re.sub(r'<script[^>]*>[\s\S]*?</script>', '', html, flags=re.IGNORECASE)
    text = re.sub(r'<style[^>]*>[\s\S]*?</style>', '', text, flags=re.IGNORECASE)
    text = re.sub(r'<(nav|footer|header|aside)[^>]*>[\s\S]*?</\1>', '', text, flags=re.IGNORECASE)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'&nbsp;', ' ', text)
    text = re.sub(r'&amp;', '&', text)
    text = re.sub(r'&lt;', '<', text)
    text = re.sub(r'&gt;', '>', text)
    text = re.sub(r'&quot;', '"', text)
    text = re.sub(r'&#39;', "'", text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def extract_title(html: str) -> str:
    match = re.search(r'<title[^>]*>([^<]+)</title>', html, re.IGNORECASE)
    return match.group(1).strip() if match else ""


@router.post("/ingest-url")
async def ingest_url(req: DirectIngestRequest):
    """Fetch a URL, clean HTML, and ingest into ChromaDB."""
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(req.url, headers={
                "User-Agent": "ResearchAssistant/1.0"
            })
            response.raise_for_status()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch URL: {e}")

    html = response.text
    title = extract_title(html)
    raw_text = strip_html(html)

    if len(raw_text) < 100:
        # Try allorigins proxy for JS-rendered pages
        try:
            proxy_url = f"https://api.allorigins.win/raw?url={req.url}"
            async with httpx.AsyncClient(timeout=30.0) as client:
                proxy_response = await client.get(proxy_url)
                proxy_response.raise_for_status()
                raw_text = strip_html(proxy_response.text)
                if not title:
                    title = extract_title(proxy_response.text)
        except httpx.HTTPError:
            pass

    if len(raw_text) < 100:
        raise HTTPException(status_code=400, detail="Could not extract meaningful content from URL")

    chunks = chunk_text(raw_text)
    count = upsert_chunks(url=req.url, chunks=chunks, title=title)

    return {
        "status": "success",
        "chunks_added": count,
        "url": req.url,
        "title": title,
    }
