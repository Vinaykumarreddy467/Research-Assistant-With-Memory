# Research Assistant With Memory

> Drop URLs, ask questions across all of them like they are one document.

A grounded, citation-backed RAG (Retrieval-Augmented Generation) system. URLs are scraped and ingested via an n8n webhook pipeline, embedded and stored in ChromaDB, and queried through a React + FastAPI chat interface powered by Claude. Every answer is traceable back to the source URL it came from, with an explicit "not found in sources" fallback instead of hallucination.

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Tech Stack](#tech-stack)
- [System Flow](#system-flow)
- [Directory Structure](#directory-structure)
- [Data Model](#data-model)
- [API Reference](#api-reference)
- [n8n Ingestion Workflow](#n8n-ingestion-workflow)
- [Environment Variables](#environment-variables)
- [Setup & Run](#setup--run)
- [Design Decisions](#design-decisions)
- [Known Limitations](#known-limitations)
- [Roadmap](#roadmap)

---

## Architecture Overview

```
                         ┌─────────────────────────────────────────────┐
                         │                   USER                       │
                         └───────────────────┬───────────────────────┬─┘
                                              │                       │
                              submits URL(s)  │                       │  asks question
                                              ▼                       ▼
                         ┌─────────────────────────┐   ┌───────────────────────────┐
                         │   n8n (Ingestion)        │   │   React Frontend (Vite)   │
                         │   Webhook trigger         │   │   Chat UI + Source panel  │
                         └────────────┬─────────────┘   └──────────────┬─────────────┘
                                      │                                │
                          scrape/clean │                     REST calls │ (fetch/SSE)
                                      ▼                                ▼
                         ┌─────────────────────────────────────────────────┐
                         │                FastAPI Backend                   │
                         │  ┌───────────────┐  ┌───────────────────────┐   │
                         │  │ /ingest       │  │ /query                │   │
                         │  │ /sources      │  │ /export-pdf           │   │
                         │  └───────┬───────┘  └───────────┬────────────┘   │
                         └──────────┼──────────────────────┼────────────────┘
                                    │                       │
                     chunk + embed  │                       │  retrieve top-k chunks
                                    ▼                       ▼
                         ┌─────────────────────┐   ┌─────────────────────────┐
                         │ OpenAI Embeddings API │   │      ChromaDB            │
                         │ text-embedding-3-small│◄─►│  persistent local store  │
                         └─────────────────────┘   └─────────────────────────┘
                                                              │
                                                  relevant chunks + metadata
                                                              ▼
                                                    ┌───────────────────────┐
                                                    │     Claude API         │
                                                    │  grounded answer +     │
                                                    │  citations             │
                                                    └───────────────────────┘
```

**Core principle:** the FastAPI backend is the only component that talks to ChromaDB, OpenAI, and Claude. n8n and React never touch the database or model APIs directly — they only call FastAPI's REST endpoints. This keeps API keys server-side and gives you one place to change the RAG logic.

---

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| Ingestion pipeline | **n8n** | Webhook receiver, URL scraping/cleaning, triggers backend ingestion |
| Backend API | **FastAPI** (Python, async) | REST endpoints, orchestrates embedding, retrieval, generation, PDF export |
| Embeddings | **OpenAI Embeddings API** (`text-embedding-3-small`) | Converts text chunks and queries into vectors |
| Vector store | **ChromaDB** (persistent client) | Stores chunk embeddings + metadata (source URL, chunk index, ingested_at) |
| LLM | **Claude API** (Anthropic) | Generates grounded answers with citations from retrieved chunks |
| Frontend | **React** (Vite) | Chat interface, source citation display, PDF download trigger |
| Config | **python-dotenv** | Loads API keys and settings from `.env` |
| PDF export | **reportlab** or **weasyprint** | Renders full Q&A session to a downloadable PDF |

---

## System Flow

### 1. Ingestion (adding a new URL)

1. User submits a URL (via n8n form trigger, or React sends it to n8n's webhook).
2. n8n's **Webhook** node receives `{ "url": "..." }`.
3. n8n scrapes the page (HTTP Request node; headless-browser node as fallback for JS-rendered pages).
4. n8n cleans HTML → plain text (Function/Code node — strip nav, footer, scripts).
5. n8n calls FastAPI's `POST /ingest` with `{ url, raw_text }`.
6. FastAPI:
   - Chunks text (~500 tokens, ~15% overlap).
   - Calls OpenAI Embeddings API per chunk.
   - Upserts vectors into ChromaDB with metadata: `{ source_url, chunk_index, title, ingested_at }`.
7. Existing sources are untouched — Chroma is additive by design (persistent collection, no wipe).

### 2. Query (asking a question)

1. User types a question in the React chat UI.
2. React calls `POST /query` with `{ question, session_id }`.
3. FastAPI:
   - Embeds the question.
   - Queries ChromaDB for top-k most similar chunks (with metadata).
   - Builds a prompt: retrieved chunks (each tagged with its source URL) + the question.
   - Calls Claude API with strict instructions: **answer only from provided chunks; cite the source URL per claim; if no chunk supports the answer, say so explicitly.**
4. FastAPI returns `{ answer, citations: [{ url, snippet }] }` to React.
5. React renders the answer with inline citation markers linking to source URLs, and appends the exchange to session history.

### 3. Export

1. User clicks "Download PDF" in React.
2. React calls `POST /export-pdf` with the full session's Q&A history.
3. FastAPI renders the transcript (questions, answers, citations) into a PDF and streams it back as a file download.

---

## Directory Structure

```
research-assistant/
├── backend/
│   ├── main.py                # FastAPI app, route definitions
│   ├── routers/
│   │   ├── ingest.py           # POST /ingest
│   │   ├── query.py            # POST /query
│   │   ├── sources.py          # GET /sources
│   │   └── export.py           # POST /export-pdf
│   ├── core/
│   │   ├── chunking.py         # text splitting logic
│   │   ├── embeddings.py       # OpenAI embedding calls
│   │   ├── retrieval.py        # ChromaDB query logic
│   │   ├── generation.py       # Claude API call + citation prompt
│   │   └── pdf_export.py       # session → PDF renderer
│   ├── models/
│   │   └── schemas.py          # Pydantic request/response models
│   ├── chroma_data/             # persistent ChromaDB storage (gitignored)
│   ├── .env                     # API keys (gitignored)
│   ├── .env.example
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── components/
│   │   │   ├── ChatWindow.jsx
│   │   │   ├── MessageBubble.jsx
│   │   │   ├── SourceCitation.jsx
│   │   │   ├── UrlIngestForm.jsx
│   │   │   └── ExportButton.jsx
│   │   ├── api.js               # fetch wrapper to FastAPI
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
│
├── n8n/
│   └── ingestion-workflow.json  # exported n8n workflow
│
├── docker-compose.yml            # optional: run backend + frontend + n8n together
└── README.md
```

---

## Data Model

### ChromaDB collection: `sources`

Each chunk is stored as one Chroma entry:

| Field | Type | Description |
|---|---|---|
| `id` | string | `{url_hash}_{chunk_index}` |
| `embedding` | vector | OpenAI `text-embedding-3-small` output (1536-dim) |
| `document` | string | the chunk text itself |
| `metadata.source_url` | string | original URL |
| `metadata.title` | string | page title if extracted |
| `metadata.chunk_index` | int | position within the source document |
| `metadata.ingested_at` | ISO timestamp | when it was added |

This metadata is what makes citations possible — every chunk Claude sees carries its source URL, and the generation prompt requires Claude to cite that URL for any claim drawn from it.

---

## API Reference

### `POST /ingest`
Called by n8n after scraping a URL.

**Request:**
```json
{
  "url": "https://example.com/article",
  "raw_text": "full scraped page text..."
}
```
**Response:**
```json
{ "status": "success", "chunks_added": 14, "url": "https://example.com/article" }
```

### `POST /query`
Called by the React frontend for each user question.

**Request:**
```json
{ "question": "What did the article say about X?", "top_k": 5 }
```
**Response:**
```json
{
  "answer": "According to the source, X is ...",
  "citations": [
    { "url": "https://example.com/article", "snippet": "relevant excerpt..." }
  ],
  "found_in_sources": true
}
```
If no relevant chunks are found above a similarity threshold, `found_in_sources: false` and the answer is a plain "not found in the ingested sources" message — no fallback to the model's general knowledge.

### `GET /sources`
Returns the list of ingested URLs (for a sidebar showing "what's in the knowledge base").

**Response:**
```json
{ "sources": [{ "url": "...", "ingested_at": "...", "chunk_count": 14 }] }
```

### `POST /export-pdf`
Renders the current session's Q&A history to PDF.

**Request:**
```json
{ "session_history": [{ "question": "...", "answer": "...", "citations": [...] }] }
```
**Response:** `application/pdf` file stream.

---

## n8n Ingestion Workflow

```
[Webhook: POST /webhook/ingest-url]
        │
        ▼
[HTTP Request: fetch the URL]
        │
        ▼
[Code node: strip HTML → clean text]
        │  (fallback branch: if content looks empty/JS-rendered,
        │   route to a headless-browser / reader-API node instead)
        ▼
[HTTP Request: POST to FastAPI /ingest]
        │
        ▼
[Respond to Webhook: 200 OK]
```

Export this as `n8n/ingestion-workflow.json` so it's versioned alongside the code.

---

## Environment Variables

`backend/.env`:
```env
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
CHROMA_PERSIST_DIR=./chroma_data
CHROMA_COLLECTION_NAME=sources
EMBEDDING_MODEL=text-embedding-3-small
CLAUDE_MODEL=claude-sonnet-4-6
TOP_K_RESULTS=5
SIMILARITY_THRESHOLD=0.35
CORS_ALLOWED_ORIGIN=http://localhost:5173
```

`frontend/.env`:
```env
VITE_API_BASE_URL=http://localhost:8000
```

---

## Setup & Run

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in your keys
uvicorn main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### n8n
```bash
npx n8n
# import n8n/ingestion-workflow.json via the n8n UI
# point its final HTTP Request node at http://localhost:8000/ingest
```

Once all three are running: submit a URL through n8n's webhook (or a form pointing at it), then open the React app at `http://localhost:5173` and start asking questions.

---

## Design Decisions

- **FastAPI as the single gatekeeper to Chroma/OpenAI/Claude** — keeps secrets server-side, gives one place to tune retrieval/prompting logic, and lets n8n and React stay "dumb" clients.
- **Persistent ChromaDB client, additive by design** — ingesting new URLs never wipes or re-indexes existing collections, satisfying the "no losing prior sources" requirement.
- **Citation-or-refuse prompting** — the Claude system prompt explicitly instructs: only answer from retrieved chunks, cite the source URL per claim, and say "not found in sources" if retrieval returns nothing above the similarity threshold. This is enforced at the prompt level, not just requested — combined with a similarity-score cutoff before chunks are even passed to Claude.
- **Chunking with overlap** — prevents facts from being split across chunk boundaries and lost during retrieval.

## Known Limitations

- Scraping is HTTP-only by default; JS-heavy sites need the headless-browser fallback branch in n8n.
- No per-user auth in v1 — single shared knowledge base.
- No streaming responses in v1 (full answer returned at once); can be added via SSE later.
- PDF export covers the current session only, not the full source archive.

## Roadmap

- [ ] Streaming answers (SSE) from `/query`
- [ ] Per-user/session isolation with auth
- [ ] Source deduplication (re-ingesting the same URL updates rather than duplicates)
- [ ] Deploy via `docker-compose` (backend + frontend + n8n in one stack)
