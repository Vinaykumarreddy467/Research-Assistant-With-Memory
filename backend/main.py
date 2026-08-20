import os
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import ingest, query, sources, export
from core.providers import get_active_provider, GROQ_API_KEY, GROQ_MODEL, OLLAMA_MODEL

app = FastAPI(title="Research Assistant API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("CORS_ALLOWED_ORIGIN", "http://localhost:5173")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingest.router)
app.include_router(query.router)
app.include_router(sources.router)
app.include_router(export.router)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/provider")
async def provider_info():
    """Return which LLM provider is active and available options."""
    active = get_active_provider()
    return {
        "active": active,
        "groq": {
            "available": bool(GROQ_API_KEY),
            "model": GROQ_MODEL if GROQ_API_KEY else None,
        },
        "ollama": {
            "available": True,
            "model": OLLAMA_MODEL,
        },
    }
