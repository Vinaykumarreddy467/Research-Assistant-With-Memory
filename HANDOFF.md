# Research Assistant With Memory - Project Handoff

**GitHub:** https://github.com/Vinaykumarreddy467/Research-Assistant-With-Memory
**Local Path:** `/home/mikealson/Desktop/Research_Assistant_With_Memory`
**Date:** August 20, 2026

---

## 1. What This Project Is

A **RAG (Retrieval-Augmented Generation)** system that:
1. Accepts URLs, scrapes & cleans web pages
2. Chunks text, embeds it into ChromaDB (vector database)
3. Answers questions using retrieved chunks + LLM, with source citations

**Tech Stack:** Python 3.11 / FastAPI / ChromaDB / React+Vite / n8n / Ollama (local LLMs) / Groq (cloud LLM, optional)

---

## 2. Architecture Overview

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Frontend   │────▶│  n8n (Docker)│────▶│   Backend    │
│  React+Vite  │     │  Webhook     │     │   FastAPI    │
│  :5173       │     │  :5678       │     │   :8000      │
└──────┬───────┘     └──────────────┘     └──────┬───────┘
       │                                          │
       │  (fallback when n8n down)                │
       └──────────────────────────────────────────┘
                                                 │
                                          ┌──────┴───────┐
                                          │              │
                                    ┌─────▼─────┐  ┌────▼────┐
                                    │ ChromaDB  │  │ Ollama  │
                                    │ (embed +  │  │ :11434  │
                                    │  search)  │  │         │
                                    └───────────┘  └─────────┘
```

### Data Flow (URL Ingestion):
1. User pastes URL in frontend
2. Frontend tries **n8n webhook** first (`POST http://localhost:5678/webhook/ingest-url`)
3. n8n fetches URL → cleans HTML → checks content → falls back to allorigins proxy if thin → POSTs `{url, raw_text}` to backend `/ingest`
4. Backend chunks text → embeds via Ollama → stores in ChromaDB
5. If n8n is down, frontend **falls back** to backend's `/ingest-url` (does fetch + clean internally)

### Data Flow (Query):
1. User asks question in chat
2. Frontend sends `POST /api/query {question, top_k: 5}`
3. Backend embeds question → searches ChromaDB → filters by similarity threshold (0.35) → sends chunks + question to LLM
4. LLM generates answer with `[Source N]` citations
5. Response returned with answer + citations + source URLs

---

## 3. Services & Ports

| Service    | Port  | Docker?   | Purpose                          |
|------------|-------|-----------|----------------------------------|
| Frontend   | 5173  | Dev server| React+Vite UI                    |
| Backend    | 8000  | Direct    | FastAPI RAG engine               |
| n8n        | 5678  | Docker    | URL ingestion workflow            |
| Ollama     | 11434 | Docker    | Local LLM + embeddings           |

---

## 4. LLM Provider System

**File:** `backend/core/providers.py`

### Priority:
1. **Groq** (cloud) — if `GROQ_API_KEY` is set in `.env`, try first (fast, free tier)
2. **Ollama** (local) — always available as fallback

### Automatic Fallback Triggers:
- Groq rate limit (429) → Ollama
- Groq token limit exceeded → Ollama
- Groq connection error → Ollama

### Current Config (`backend/.env`):
```
GROQ_API_KEY=                          # Empty = Ollama only
GROQ_MODEL=llama-3.3-70b-versatile
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b               # For answer generation
EMBEDDING_MODEL=qwen3-embedding:8b     # For text embeddings
```

### To enable Groq:
Add your API key to `backend/.env`:
```
GROQ_API_KEY=gsk_...
```
Restart backend. The frontend will show "⚡ Groq" instead of "🏠 Ollama".

---

## 5. How to Run Everything

### Start Backend:
```bash
cd /home/mikealson/Desktop/Research_Assistant_With_Memory/backend
source venv/bin/activate
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

### Start Frontend:
```bash
cd /home/mikealson/Desktop/Research_Assistant_With_Memory/frontend
npm run dev
```

### n8n (Docker):
```bash
docker compose up n8n
```
- Open `http://localhost:5678` in browser
- Import workflow from `n8n/ingestion-workflow.json`
- **Activate the workflow** (toggle Active ON in top-right corner of editor)

### Ollama (Docker):
```bash
docker compose up ollama
```
Models needed (pull manually if not present):
```bash
docker exec -it <ollama-container> ollama pull qwen3-embedding:8b
docker exec -it <ollama-container> ollama pull llama3.2:3b
```

### Full Docker Compose:
```bash
docker compose up --build
```

---

## 6. Backend API Endpoints

### `POST /ingest` — Ingest pre-scraped text (used by n8n)
```json
Request:  { "url": "...", "raw_text": "...", "title": "..." }
Response: { "status": "success", "chunks_added": 5, "url": "..." }
```

### `POST /ingest-url` — Fetch URL directly, no n8n needed
```json
Request:  { "url": "..." }
Response: { "status": "success", "chunks_added": 5, "url": "...", "title": "..." }
```
- Tries direct HTTP fetch first
- Falls back to allorigins proxy if content is thin
- Rejects if < 100 chars extracted (JS-rendered pages)

### `POST /query` — Ask a question
```json
Request:  { "question": "...", "top_k": 5 }
Response: {
  "answer": "...",
  "citations": [{"url": "...", "snippet": "..."}],
  "found_in_sources": true
}
```

### `GET /sources` — List all ingested sources
```json
Response: {
  "sources": [
    {"url": "...", "ingested_at": "...", "chunk_count": 3}
  ]
}
```

### `GET /provider` — Which LLM is active
```json
Response: {
  "active": "ollama",
  "groq": {"available": false, "model": null},
  "ollama": {"available": true, "model": "llama3.2:3b"}
}
```

### `GET /health` — Health check
```json
Response: { "status": "ok" }
```

### `POST /export-pdf` — Export chat session as PDF
```json
Request:  { "session_history": [{"question": "...", "answer": "...", "citations": [...]}] }
Response: PDF file (application/pdf)
```

---

## 7. n8n Workflow

**File:** `n8n/ingestion-workflow.json`

### Pipeline Nodes:
1. **Webhook** — receives `POST /webhook/ingest-url` with `{url}`
2. **Fetch URL** — HTTP GET with 30s timeout, follows redirects
3. **Clean HTML** — JS code node: strips tags, scripts, styles, nav/footer, decodes entities, collapses whitespace
4. **Content OK?** — If text < 200 chars (JS-rendered page), branches to fallback
5. **Fallback Fetch** — Fetches via `api.allorigins.win` proxy
6. **Clean Fallback HTML** — Same cleaning as step 3
7. **POST to FastAPI /ingest** — Sends `{url, raw_text}` to backend
8. **Respond 200 OK** / **Respond Error** — Returns JSON response

### Webhook URLs:
- **Test mode:** `http://localhost:5678/webhook-test/ingest-url` (one-shot, must click "Execute Workflow" each time)
- **Production:** `http://localhost:5678/webhook/ingest-url` (persistent, requires workflow Active)

---

## 8. Frontend Architecture

**Stack:** React 19 + Vite + CSS (dark theme)

### Components:
| Component       | File                              | Purpose                         |
|-----------------|-----------------------------------|---------------------------------|
| App             | `src/App.jsx`                     | Main layout, state management   |
| ChatWindow      | `src/components/ChatWindow.jsx`   | Chat interface with messages    |
| MessageBubble   | `src/components/MessageBubble.jsx`| Renders user/assistant messages |
| UrlIngestForm   | `src/components/UrlIngestForm.jsx`| URL input form                 |
| SourceCitation  | `src/components/SourceCitation.jsx`| Clickable citation links       |
| SourcesList     | `src/components/SourcesList.jsx`  | Sidebar showing all sources     |
| ExportButton    | `src/components/ExportButton.jsx` | PDF export button               |

### API Layer (`src/api.js`):
- All API calls go through `/api` (Vite proxy → `localhost:8000`)
- `ingestUrl()` tries n8n webhook first, falls back to `/api/ingest-url`

### Vite Config:
- Dev server on port 5173
- Proxy: `/api/*` → `http://localhost:8000/*`

---

## 9. File Structure

```
Research_Assistant_With_Memory/
├── README.md
├── docker-compose.yml
├── n8n/
│   └── ingestion-workflow.json          # n8n workflow definition
├── backend/
│   ├── main.py                          # FastAPI app entry
│   ├── .env                             # Config (Groq key, Ollama model, etc.)
│   ├── requirements.txt                 # Python dependencies
│   ├── Dockerfile
│   ├── chroma_data/                     # ChromaDB persistent storage
│   ├── venv/                            # Python virtual environment
│   ├── core/
│   │   ├── __init__.py
│   │   ├── chunking.py                  # Word-based text chunking (500 words, 75 overlap)
│   │   ├── embeddings.py                # Ollama embedding via /api/embed
│   │   ├── generation.py                # LLM answer generation with citation extraction
│   │   ├── providers.py                 # Groq/Ollama provider with automatic fallback
│   │   ├── pdf_export.py                # ReportLab PDF generation
│   │   └── retrieval.py                 # ChromaDB upsert/query/sources
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py                   # Pydantic request/response models
│   └── routers/
│       ├── __init__.py
│       ├── direct_ingest.py             # POST /ingest-url (fetch + clean + ingest)
│       ├── export.py                    # POST /export-pdf
│       ├── ingest.py                    # POST /ingest (receives from n8n)
│       ├── query.py                     # POST /query
│       └── sources.py                   # GET /sources
└── frontend/
    ├── index.html
    ├── package.json
    ├── package-lock.json
    ├── vite.config.js
    ├── Dockerfile
    ├── nginx.conf
    ├── .env
    └── src/
        ├── main.jsx
        ├── App.jsx                      # Main app component
        ├── App.css                      # Dark theme styles
        ├── index.css                    # CSS variables
        ├── api.js                       # API functions (n8n + backend)
        └── components/
            ├── ChatWindow.jsx
            ├── ExportButton.jsx
            ├── MessageBubble.jsx
            ├── SourceCitation.jsx
            ├── SourcesList.jsx
            └── UrlIngestForm.jsx
```

---

## 10. Git History (12 commits)

```
f7277ce Fix 10 bugs found in code review
6e866d2 Fix direct ingest timeouts, improve error handling
bae2efd Fix frontend session history, add direct URL ingest endpoint (no n8n needed)
ea4f19d Fix Ollama timeout (300s), switch default LLM to llama3.2:3b for speed
608a357 Add Docker setup: backend, frontend, n8n, ollama
63abb92 Add React + Vite frontend with chat UI, URL ingest, source panel
1d642d9 Add Groq + Ollama provider with automatic fallback
591b525 Switch backend to Ollama (qwen3-embedding + qwen3.5) for offline use
fee8225 Add FastAPI backend: ingest, query, sources, PDF export endpoints
3a9e704 Add n8n URL ingestion workflow
953bbdb Add project README
079170d Initial commit: add .gitignore
```

---

## 11. Configuration Options

### Change LLM Model:
Edit `backend/.env`:
```
OLLAMA_MODEL=llama3.1:latest     # or llama3.1:8b, qwen3.5:latest, etc.
```
Pull the model first: `docker exec -it <container> ollama pull <model>`

### Change Embedding Model:
Edit `backend/.env`:
```
EMBEDDING_MODEL=qwen3-embedding:4b    # smaller, faster
EMBEDDING_MODEL=nomic-embed-text      # lightweight alternative
```

### Adjust Chunk Size:
Edit `backend/core/chunking.py` line 4:
```python
def chunk_text(text: str, chunk_size: int = 500, overlap: int = 75):
```

### Adjust Similarity Threshold:
Edit `backend/.env`:
```
SIMILARITY_THRESHOLD=0.35    # Higher = stricter matching
```

### CORS (if accessing from different origin):
Edit `backend/.env`:
```
CORS_ALLOWED_ORIGIN=http://localhost:5173
```

---

## 12. Known Limitations & TODOs

### Current Issues:
1. **JS-rendered pages** — Pages that render content via JavaScript return thin HTML. The allorigins proxy helps but doesn't solve all cases.
2. **Embedding speed** — `qwen3-embedding:8b` is slow on CPU (~30s per large page). Consider `qwen3-embedding:4b` or `nomic-embed-text` for faster embedding.
3. **Chunking is word-based** — Doesn't respect paragraph or section boundaries. Consider semantic chunking.
4. **Citation format** — LLM sometimes uses `(Source 1)` instead of `[Source 1]`, breaking citation parsing.
5. **No authentication** — Backend is open, no user auth.
6. **No session persistence** — Chat history resets on page reload.
7. **n8n activation** — Workflow must be manually activated after container restart.

### Potential Improvements:
- Add file upload (PDF, TXT, DOCX) alongside URL ingestion
- Add streaming responses from LLM
- Add conversation memory (multi-turn context)
- Add more embedding models for comparison
- Add search within ingested sources (pre-LLM)
- Add rate limiting on backend
- Add Docker health checks

---

## 13. Useful Commands

```bash
# Test backend health
curl http://localhost:8000/health

# Test n8n webhook (production - must be active)
curl -X POST http://localhost:5678/webhook/ingest-url \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'

# Ingest URL directly (no n8n)
curl -X POST http://localhost:8000/ingest-url \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'

# Query
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What is X?", "top_k": 3}'

# List sources
curl http://localhost:8000/sources

# Check provider
curl http://localhost:8000/provider

# Check Ollama models
curl http://localhost:11434/api/tags

# Start everything (from project root)
docker compose up -d ollama
# Wait for ollama, then start backend + frontend outside docker
cd backend && source venv/bin/activate && python -m uvicorn main:app --port 8000 &
cd frontend && npm run dev &
```

---

## 14. Python Dependencies

```
fastapi==0.115.6
uvicorn[standard]==0.34.0
python-dotenv==1.0.1
chromadb==0.5.23
httpx==0.28.1
pydantic==2.10.4
reportlab==4.2.5
```

---

*Handoff created August 20, 2026*
