# Research Assistant With Memory - Project Handoff

**GitHub:** https://github.com/Vinaykumarreddy467/Research-Assistant-With-Memory
**Local Path:** `/home/mikealson/Desktop/Research_Assistant_With_Memory`
**Date:** August 24, 2026

---

## 1. What This Project Is

A **RAG (Retrieval-Augmented Generation)** system that:
1. Accepts URLs, scrapes & cleans web pages (via n8n or direct fallback)
2. Chunks text, embeds it into ChromaDB (vector database)
3. Keeps chat history and sessions in an SQLite database (persistent conversation memory)
4. Answers questions using retrieved chunks + LLM (with source citations) and automatically strips thinking/reasoning tags
5. Exposes a premium React web interface and a python-native Streamlit dashboard

**Tech Stack:** Python 3.11 / FastAPI / ChromaDB / SQLite / React+Vite / Streamlit / n8n / Ollama (local LLMs) / Groq (cloud LLM, preferred)

---

## 2. Architecture Overview

```
                         ┌──────────────────────────────────────────────┐
                         │                   USER                       │
                         └─────┬──────────────────────────────────┬─────┘
                               │                                  │
                               │ submits URL(s)                   │ asks question
                               ▼                                  ▼
                 ┌─────────────┴───────────┐          ┌───────────┴──────────────┐
                 │   n8n (Ingestion)       │          │   Frontends:             │
                 │   Webhook trigger       │          │   - React UI (Port 5173) │
                 └─────────────┬───────────┘          │   - Streamlit (Port 8501)│
                               │                      └───────────┬──────────────┘
                  scrape/clean │                                  │ REST calls
                               ▼                                  ▼
                 ┌──────────────────────────────────────────────────────────────┐
                 │                       FastAPI Backend                        │
                 │  ┌────────────────────────┐      ┌────────────────────────┐  │
                 │  │ /ingest & /ingest-url  │      │ /query                 │  │
                 │  │ /sources               │      │ /sessions & /messages  │  │
                 │  └───────────┬────────────┘      └───────────┬────────────┘  │
                 └──────────────┼───────────────────────────────┼───────────────┘
                                │                               │
                 chunk & embed  │                               │ retrieve top-k chunks
                                ▼                               ▼
                 ┌──────────────┴───────────┐      ┌────────────┴─────────────┐
                 │   Ollama Local API       │◄────►│   ChromaDB               │
                 │   nomic-embed-text       │      │   persistent local store │
                 └──────────────────────────┘      └──────────────────────────┘
                                                                │
                                                    relevant chunks + metadata
                                                                ▼
                                                   ┌────────────┴─────────────┐
                                                   │    LLM Providers:        │
                                                   │    - Groq (Cloud - Pref) │
                                                   │    - Ollama (Local - FB) │
                                                   └──────────────────────────┘
```

### Data Flow (URL Ingestion):
1. User pastes URL in frontend (React or Streamlit)
2. Frontend tries **n8n webhook** first (`POST http://localhost:5678/webhook/ingest-url`)
3. n8n fetches URL → cleans HTML → checks content -> falls back to allorigins proxy if thin → POSTs `{url, raw_text, title}` to backend `/ingest`
4. Backend chunks text → embeds via Ollama → stores in ChromaDB
5. If n8n is down/unavailable, frontend/backend **falls back** to backend's `/ingest-url` (does fetch + clean + proxy fallback internally)

### Data Flow (Query):
1. User asks question in chat
2. Frontend sends `POST /query {question, session_id, top_k: 5}`
3. Backend fetches previous chat history from SQLite (messages table)
4. Backend embeds question → searches ChromaDB (optionally scoped to a specific source URL) → filters by similarity threshold (0.35) → sends chunks + question + chat history to LLM
5. LLM generates answer using Groq (or Ollama fallback)
6. Backend strips out reasoning process tags (e.g. `<think>...</think>`) and returns the grounded answer + citations
7. Response is logged to SQLite and returned to UI

---

## 3. Services & Ports

| Service    | Port  | Runner / Tech | Purpose                             |
|------------|-------|---------------|-------------------------------------|
| Frontend   | 5173  | React + Vite  | Premium dev server React UI         |
| Streamlit  | 8501  | Streamlit     | Alternative Python-native Dashboard |
| Backend    | 8000  | FastAPI       | Core RAG engine, SQLite, & orchestrator|
| n8n        | 5678  | Docker        | Advanced URL scraping pipeline     |
| Ollama     | 11434 | Docker        | Local embedding + fallback LLM      |

---

## 4. LLM Provider System

**File:** `backend/core/providers.py`

### Priority:
1. **Groq** (cloud) — if `GROQ_API_KEY` is set in `.env`, try first (fast, free tier)
2. **Ollama** (local) — always available as fallback

### Automatic Fallback Triggers:
- Groq rate limit (429) → Ollama
- Groq token limit exceeded → Ollama
- Groq connection error / unreachable → Ollama

### Current Config (`backend/.env`):
```env
GROQ_API_KEY=gsk_...
GROQ_MODEL=qwen/qwen3.6-27b
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b
EMBEDDING_MODEL=nomic-embed-text:latest
```

---

## 5. How to Run Everything

### The Automated Script Way (Recommended)
We have custom bash scripts in the root directory to automate running and stopping all developer services:
```bash
# Start Backend, React Frontend, and Streamlit Dashboard
./run.sh

# Monitor live log outputs
tail -f backend.log frontend.log streamlit.log

# Stop all processes cleanly
./stop.sh
```

### The Manual Way

#### Start Backend:
```bash
cd backend
source venv/bin/activate
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

#### Start React Frontend:
```bash
cd frontend
npm run dev
```

#### Start Streamlit Dashboard:
```bash
cd streamlit
source venv/bin/activate
streamlit run app.py --server.port 8501
```

#### n8n (Docker):
```bash
docker compose up n8n
```
- Open `http://localhost:5678` in browser
- Import workflow from `n8n/ingestion-workflow.json`
- **Activate the workflow** (toggle Active ON in the top-right corner of the editor)

#### Ollama (Docker):
```bash
docker compose up ollama
```
Models needed (pull manually if not present):
```bash
docker exec -it <ollama-container> ollama pull nomic-embed-text:latest
docker exec -it <ollama-container> ollama pull llama3.2:3b
```

---

## 6. Backend API Endpoints

### Ingestion & Search

#### `POST /ingest` — Ingest pre-scraped text (used by n8n)
```json
Request:  { "url": "...", "raw_text": "...", "title": "..." }
Response: { "status": "success", "chunks_added": 5, "url": "..." }
```

#### `POST /ingest-url` — Fetch URL directly, no n8n needed
```json
Request:  { "url": "..." }
Response: { "status": "success", "chunks_added": 5, "url": "...", "title": "..." }
```
- Tries direct HTTP fetch first
- Falls back to allorigins proxy if content is thin
- Rejects if < 100 chars extracted (JS-rendered pages)

#### `POST /query` — Ask a question
```json
Request:  { "question": "...", "session_id": "optional-uuid", "top_k": 5 }
Response: {
  "answer": "...",
  "citations": [{"url": "...", "snippet": "..."}],
  "found_in_sources": true,
  "provider": "groq"
}
```

#### `GET /sources` — List all unique ingested sources
```json
Response: {
  "sources": [
    {"url": "...", "ingested_at": "...", "chunk_count": 3}
  ]
}
```

#### `GET /provider` — Which LLM is active
```json
Response: {
  "active": "groq",
  "groq": {"available": true, "model": "qwen/qwen3.6-27b"},
  "ollama": {"available": true, "model": "llama3.2:3b"}
}
```

#### `GET /health` — Health check
```json
Response: { "status": "ok" }
```

#### `POST /export-pdf` — Export chat session as PDF
```json
Request:  { "session_history": [{"question": "...", "answer": "...", "citations": [...]}] }
Response: PDF file (application/pdf)
```

### Chat Session Management (SQLite persistent backend)

#### `GET /sessions` — List all active conversation sessions
```json
Response: [
  { "id": "uuid-string", "title": "Conversation Name", "source_url": "scoped_url_or_null", "created_at": "..." }
]
```

#### `POST /sessions` — Create a new conversation session
```json
Request:  { "title": "New Chat Title", "source_url": "optional_url_to_scope_chat" }
Response: { "id": "uuid-string", "title": "New Chat Title", "source_url": "...", "created_at": "..." }
```

#### `GET /sessions/{session_id}/messages` — Get session messages
```json
Response: [
  { "id": 1, "session_id": "uuid-string", "role": "user", "content": "Question text...", "citations": [], "created_at": "..." },
  { "id": 2, "session_id": "uuid-string", "role": "assistant", "content": "Response text...", "citations": [...], "created_at": "..." }
]
```

#### `DELETE /sessions/{session_id}` — Delete a session and its message history
```json
Response: { "status": "success", "message": "Session uuid-string deleted" }
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
7. **POST to FastAPI /ingest** — Sends `{url, raw_text, title}` to backend
8. **Respond 200 OK** / **Respond Error** — Returns JSON response

---

## 8. Frontend Architectures

### 1. React Web App
* **Stack:** React 19 + Vite + CSS variables (Premium Dark Theme)
* **Path:** `frontend/`
* **Components:**
  - `App.jsx`: Main interface container, handles router, active conversation session, fetching logic.
  - `ChatWindow.jsx`: Hosts messages scroll and input boxes.
  - `MessageBubble.jsx`: Format messages, formats inline citation numbers.
  - `UrlIngestForm.jsx`: Text input for URL ingestion.
  - `SourcesList.jsx`: Sidebar showing ingested sources, links to create scoped chats.
  - `ExportButton.jsx`: Trigger endpoint for PDF download.
  - `SourceCitation.jsx`: Custom citations render block.
* **API Layer (`src/api.js`):** Wraps standard endpoint fetches. Tries n8n webhook first for URL ingestion, falling back to `/api/ingest-url`.

### 2. Streamlit Dashboard
* **Stack:** Streamlit + Requests (Python-native)
* **Path:** `streamlit/`
* **File:** `app.py`
* **UI Features:**
  - Sidebar: lists active session list with creation/deletion options, displays loaded knowledge sources with "Start scoped chat" buttons.
  - Chat Window: standard Streamlit chat components, displays citations and snippets as cards underneath messages.
  - URL Ingest Bar: direct page index form.
  - PDF Export Button: requests PDF buffer and downloads it natively.

---

## 9. File Structure

```
Research_Assistant_With_Memory/
├── README.md
├── docker-compose.yml
├── run.sh
├── stop.sh
├── n8n/
│   └── ingestion-workflow.json          # n8n workflow definition
├── streamlit/
│   ├── app.py                           # Streamlit code
│   ├── requirements.txt                 # Streamlit packages
│   └── Dockerfile
├── backend/
│   ├── main.py                          # FastAPI app entry
│   ├── .env                             # Config
│   ├── requirements.txt                 # Python dependencies
│   ├── Dockerfile
│   ├── chroma_data/                     # ChromaDB and SQLite persistent files
│   ├── core/
│   │   ├── __init__.py
│   │   ├── chunking.py                  # Word-based text chunking (500 words, 75 overlap)
│   │   ├── db.py                        # SQLite storage helpers
│   │   ├── embeddings.py                # Ollama embeddings connector
│   │   ├── generation.py                # Prompt construction
│   │   ├── providers.py                 # LLM Orchestrator (Groq / Ollama fallback + tag stripping)
│   │   └── pdf_export.py                # PDF generation
│   ├── models/
│   │   └── schemas.py                   # Request/Response data shapes
│   └── routers/
│       ├── direct_ingest.py             # URL fetch/clean fallback router
│       ├── export.py                    # PDF download router
│       ├── ingest.py                    # Webhook scraper router
│       ├── query.py                     # Main RAG search & chat router
│       ├── sessions.py                  # Chat sessions CRUD router
│       └── sources.py                   # GET /sources router
└── frontend/
    ├── index.html
    ├── package.json
    ├── vite.config.js
    ├── src/
    │   ├── main.jsx
    │   ├── App.jsx                      # Main app component
    │   ├── App.css                      # Custom styles
    │   ├── api.js                       # API connector
    │   └── components/
    │       ├── ChatWindow.jsx
    │       ├── ExportButton.jsx
    │       ├── MessageBubble.jsx
    │       ├── SourceCitation.jsx
    │       ├── SourcesList.jsx
    │       └── UrlIngestForm.jsx
```

---

## 10. Git History (16 commits)

```
4d4086c Merge Streamlit UI + launch scripts from v1, add Docker support
14eb6e3 Increase ingest timeout in api.js
b3cf72d Add session persistence, improve frontend UX, update provider system
f91c133 Add project handoff, fix Docker networking, strip LLM reasoning tags
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
```env
OLLAMA_MODEL=llama3.1:latest     # or llama3.1:8b, qwen2.5:7b, etc.
```
Remember to pull the model: `docker exec -it <container> ollama pull <model>`

### Change Embedding Model:
Edit `backend/.env`:
```env
EMBEDDING_MODEL=nomic-embed-text:latest
```

### Adjust Similarity Threshold:
Edit `backend/.env`:
```env
SIMILARITY_THRESHOLD=0.35    # Higher = stricter relevance check
```

---

## 12. Known Limitations & TODOs

### Current Issues:
1. **JS-rendered pages** — Pages that require JavaScript to render HTML will return minimal text unless fetched through a headless browser node in n8n.
2. **Embedding speed** — Without GPU acceleration, local embeddings via Ollama can take a significant amount of CPU processing time.
3. **No authentication** — No user authentication exists; sessions are shared.

### Potential Improvements:
- Add direct file upload panel (PDF, TXT, CSV) alongside URL ingestion.
- Implement token streaming for real-time output in both frontends.
- Add user-level authentication and scoped private workspaces.

---

## 13. Useful Commands

```bash
# Test backend health
curl http://localhost:8000/health

# List sessions
curl http://localhost:8000/sessions

# Ingest URL directly (no n8n)
curl -X POST http://localhost:8000/ingest-url \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'

# Query
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What is X?", "session_id": "...", "top_k": 3}'

# Check Ollama tags
curl http://localhost:11434/api/tags
```

---

## 14. Dependencies

### Backend Python Packages
```
fastapi==0.115.6
uvicorn[standard]==0.34.0
python-dotenv==1.0.1
chromadb==0.5.23
httpx==0.28.1
pydantic==2.10.4
reportlab==4.2.5
```

### Streamlit Packages
```
streamlit>=1.38.0
requests>=2.31.0
reportlab>=4.2.0
python-dotenv>=1.0.1
```

---

*Handoff updated August 24, 2026*
