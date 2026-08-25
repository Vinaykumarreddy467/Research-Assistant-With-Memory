# Research Assistant with Memory

> Drop URLs, ask questions across all of them like they are one document.

A grounded, citation-backed RAG (Retrieval-Augmented Generation) system. Web URLs are scraped and ingested via an n8n webhook pipeline (with direct backend fallback), chunked, embedded locally via Ollama (`nomic-embed-text:latest`), and stored in ChromaDB. The system supports multi-turn chat sessions with persistence in a local SQLite database, selectable scoped search, and a premium React + Vite frontend or a Python-native Streamlit dashboard. Answers are generated using Groq (`qwen/qwen3.6-27b`) with an automatic failover to local Ollama (`llama3.2:3b`), and any reasoning/thinking tags (e.g., `<think>...</think>`) are automatically stripped. Every claim is citation-backed with a clickable reference, and PDF export allows downloading the full Q&A history.

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Tech Stack](#tech-stack)
- [System Flow](#system-flow)
- [Directory Structure](#directory-structure)
- [Data Storage Models](#data-storage-models)
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
┌─────────────────────────────────────────────────────────────────┐
│                        USER INTERFACES                          │
│                                                                 │
│  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────┐ │
│  │   React + Vite   │  │    Streamlit     │  │    n8n UI     │ │
│  │   :5173          │  │    :8501         │  │    :5678      │ │
│  │   (Main UI)      │  │   (Alt UI)       │  │  (Workflow)   │ │
│  └────────┬─────────┘  └────────┬─────────┘  └───────┬───────┘ │
└───────────┼─────────────────────┼─────────────────────┼─────────┘
            │                     │                     │
            ▼                     ▼                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                     BACKEND (FastAPI :8000)                      │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │   /query     │  │  /ingest    │  │ /ingest-url │            │
│  │  (RAG)       │  │  (from n8n) │  │ (direct)    │            │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘            │
│         │                │                │                      │
│         ▼                ▼                ▼                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │  Embeddings │  │   Chunking  │  │   HTML      │            │
│  │  (query)    │  │  (500 words)│  │   Cleaner   │            │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘            │
│         │                │                │                      │
│         ▼                ▼                ▼                      │
│  ┌─────────────────────────────────────────────────┐           │
│  │              RETRIEVAL (ChromaDB)                │           │
│  │   Store chunks + embeddings / Query similar     │           │
│  └──────────────────────┬──────────────────────────┘           │
│                         │                                       │
│                         ▼                                       │
│  ┌─────────────────────────────────────────────────┐           │
│  │            GENERATION (LLM Provider)            │           │
│  │                                                 │           │
│  │   Groq (cloud) ──fallback──▶ Ollama (local)     │           │
│  │   + LangSmith tracing (optional)                │           │
│  └─────────────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────────────┘
            │                                    │
            ▼                                    ▼
┌──────────────────────┐          ┌──────────────────────┐
│   ChromaDB           │          │   Ollama             │
│   (Vector Store)     │          │   (Local LLMs)       │
│   - Embeddings       │          │   - nomic-embed-text │
│   - Chunks           │          │   - qwen3 / llama3   │
│   - Metadata         │          │   - 11434            │
└──────────────────────┘          └──────────────────────┘
```

**Core principle:** The FastAPI backend acts as the single orchestrator. It is the only component that talks directly to ChromaDB, SQLite, Ollama, and Groq. n8n and the frontend interfaces (React and Streamlit) remain decoupled and only communicate with FastAPI's REST endpoints, keeping keys secure and the application logic centralized.

### Data Flow — URL Ingestion
```
User pastes URL
       │
       ▼
┌──────────────┐    POST /webhook/ingest-url
│   Frontend   │ ──────────────────────────────▶  n8n
│  api.js      │                                  │
└──────────────┘                                  ▼
       │                                  ┌──────────────┐
       │                                  │  Fetch URL   │
       │                                  │  (HTTP GET)  │
       │                                  └──────┬───────┘
       │                                         │
       │                                         ▼
       │                                  ┌──────────────┐
       │                                  │  Clean HTML  │
       │                                  │  (strip tags)│
       │                                  └──────┬───────┘
       │                                         │
       │                                    ┌────┴────┐
       │                                    │ Content │
       │                                    │  OK?    │
       │                                    └────┬────┘
       │                              thin ◀─────┼────▶ OK
       │                               │              │
       │                               ▼              │
       │                        ┌──────────────┐     │
       │                        │ allorigins   │     │
       │                        │ (proxy)      │     │
       │                        └──────┬───────┘     │
       │                               │              │
       │                               ▼              ▼
       │                        POST /ingest  ◀──────┘
       │                                  │
       │                                  ▼
       │                         ┌──────────────┐
       │                         │   Chunking   │
       │                         │  500 words   │
       │                         │  75 overlap  │
       │                         └──────┬───────┘
       │                                │
       │                                ▼
       │                         ┌──────────────┐
       │                         │  Embeddings  │
       │                         │  (Ollama)    │
       │                         └──────┬───────┘
       │                                │
       │                                ▼
       │                         ┌──────────────┐
       └────────────────────────▶│  ChromaDB    │
                                 │  (upsert)    │
                                 └──────────────┘
```

**Two paths to ingest:**
1. **Via n8n** — Frontend → n8n webhook → fetch & clean → backend `/ingest`
2. **Direct** — Frontend → backend `/ingest-url` (does fetch & clean itself)

### Data Flow — Query (RAG)
```
User asks: "What is agentic AI?"
       │
       ▼
┌──────────────┐
│   Frontend   │  POST /query {question, top_k, session_id}
└──────┬───────┘
       │
       ▼
┌──────────────────────────────────────────┐
│              BACKEND /query              │
│                                          │
│  1. EMBED question                       │
│     └─▶ Ollama (nomic-embed-text)        │
│         "What is agentic AI?" → [0.12, -0.34, ...]  │
│                                          │
│  2. SEARCH ChromaDB                      │
│     └─▶ Find top-5 similar chunks       │
│         Distance threshold: 0.35         │
│                                          │
│  3. FORMAT context                       │
│     [Source 1: ibm.com/think/agentic]    │
│     "Agentic AI refers to systems..."    │
│                                          │
│  4. GENERATE answer                      │
│     └─▶ Groq → (fallback) → Ollama      │
│         System: "Answer only from sources"│
│         User: context + question         │
│                                          │
│  5. EXTRACT citations                    │
│     [Source 1] → ibm.com URL + snippet   │
│                                          │
│  6. SAVE to session (SQLite)             │
│     user msg + assistant msg             │
└──────────────────────────────────────────┘
       │
       ▼
┌──────────────┐
│   Frontend   │  {answer, citations, provider}
│  ChatWindow  │
└──────────────┘
```

### Provider Fallback System
```
generate_with_fallback()
       │
       ├─── GROQ_API_KEY set? ──▶ Try Groq
       │                              │
       │                    ┌─────────┴─────────┐
       │                    │                    │
       │               Success              Failure
       │               return "groq"         │
       │                              ┌───────┴───────┐
       │                              │   429?        │
       │                              │   token?      │
       │                              │   offline?    │
       │                              └───────┬───────┘
       │                                      │
       └──────────────────────────────────────┘
                                          │
                                          ▼
                                 Try Ollama (local)
                                          │
                                   ┌──────┴──────┐
                                   │             │
                                Success      Failure → Error
                                return "ollama"
```

---

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| Ingestion Pipeline | **n8n** | Webhook receiver, URL scraping/cleaning, redirects to FastAPI ingestion |
| Backend API | **FastAPI** (Python 3.11) | REST endpoints, handles chunking, embedding, retrieval, session management, and PDF export |
| Embeddings | **Ollama** (`nomic-embed-text:latest`) | Local embedding generation for chunks and user queries |
| Vector Store | **ChromaDB** (Persistent) | Stores chunk vector embeddings and metadata (source URL, title, chunk index, timestamp) |
| Session Store | **SQLite** | Persistent relational storage for chat sessions and conversational history |
| LLM Providers | **Groq** (`qwen/qwen3.6-27b`) <br> **Ollama** (`llama3.2:3b`) | Answer generation with citations; includes auto-fallback from Groq to Ollama on errors/rate-limits |
| React UI | **React 19** (Vite) | Premium dark-themed chat interface with session management, source panel, PDF export |
| Streamlit UI | **Streamlit** | Fast, Python-native alternative chat dashboard with full feature parity |
| Configuration | **python-dotenv** | Loads API credentials and configurations from `.env` |
| PDF Export | **reportlab** | Dynamically renders session Q&A history to a downloadable PDF |
| Observability | **LangSmith** | Tracing and monitoring for the RAG query chain and LLM provider invocations |


---

## System Flow

### 1. Ingestion (Adding a new URL)
* **n8n Pipeline (Preferred):** User submits a URL. The React/Streamlit client sends it to n8n's webhook node. n8n fetches the HTML, extracts and cleans the main body text, and routes the cleaned payload to the backend's `POST /ingest` endpoint.
* **Direct Ingestion (Fallback/Direct):** If n8n is offline, the React/Streamlit app or direct REST call targets FastAPI's `POST /ingest-url`. FastAPI fetches the page, cleans it (stripping nav, footer, scripts), falls back to `api.allorigins.win` proxy if thin, and indexes the text.
* **Vector Storage:** FastAPI splits the text into chunks (~500 words, ~15% overlap), calls Ollama's local embeddings API, and upserts the vectors into ChromaDB along with metadata.

### 2. Query (Asking a question)
1. User types a query in the Chat UI under an active session.
2. The UI sends a `POST /query` request containing the `question`, `session_id`, and `top_k`.
3. FastAPI retrieves the active session details and previous conversation history from SQLite.
4. If the session is scoped to a specific source URL, FastAPI filters the ChromaDB vector search to that URL. Otherwise, it searches the entire vector space.
5. The question is embedded, and the top-k matches are retrieved. Chunks below the similarity threshold (default: `0.35`) are discarded.
6. The query, history, and filtered chunks (with source indicators) are sent to the LLM (Groq, falling back to Ollama if needed).
7. Any reasoning process tags (e.g. `<think>...</think>`) are stripped out. The LLM generates the grounded response.
8. The question and cleaned answer with citations are stored in the SQLite database, and returned to the UI.

### 3. PDF Export
1. The user clicks "Export PDF".
2. The frontend sends the structured session Q&A history to `POST /export-pdf`.
3. FastAPI generates a formatted PDF transcript using ReportLab and streams the document back to the browser.

---

## Directory Structure

```
Research_Assistant_With_Memory/
├── docker-compose.yml            # Docker setup for n8n, Ollama, and DB configs
├── run.sh                        # Automated startup script (Backend + React + Streamlit)
├── stop.sh                       # Automated stop script
├── n8n/
│   └── ingestion-workflow.json   # Exported n8n workflow definition
├── backend/
│   ├── main.py                   # FastAPI app entry point and configuration
│   ├── .env                      # API keys and environment configuration
│   ├── requirements.txt          # Python dependencies
│   ├── Dockerfile
│   ├── chroma_data/              # Local storage for ChromaDB and SQLite DB files
│   ├── core/
│   │   ├── chunking.py           # Word-based chunk splitting (500 size, 75 overlap)
│   │   ├── db.py                 # SQLite session and message storage logic
│   │   ├── embeddings.py         # Ollama embedding integration
│   │   ├── generation.py         # Prompt building and citation mapping
│   │   ├── providers.py          # Groq/Ollama APIs with automatic fallback and tag stripping
│   │   └── pdf_export.py         # ReportLab PDF creation
│   ├── models/
│   │   └── schemas.py            # Pydantic schemas (requests & responses)
│   └── routers/
│       ├── direct_ingest.py      # POST /ingest-url (direct fetch, clean, and index)
│       ├── export.py             # POST /export-pdf
│       ├── ingest.py             # POST /ingest (webhook payload processor)
│       ├── query.py              # POST /query (RAG search, chat history, LLM generation)
│       ├── sessions.py           # CRUD endpoints for persistent chat sessions
│       └── sources.py            # GET /sources (list ingested documents)
├── frontend/                     # React Vite Application
│   ├── src/
│   │   ├── App.jsx               # Layout, main state management
│   │   ├── api.js                # API client wrapper
│   │   └── components/           # Chat window, citations, source list, forms
│   ├── package.json
│   └── vite.config.js
└── streamlit/                    # Streamlit Dashboard Application
    ├── app.py                    # Streamlit app interface
    ├── requirements.txt          # Streamlit dependencies
    └── Dockerfile
```

---

## Data Storage Models

### Vector Store (ChromaDB)
Individual document chunks are embedded and indexed under the `sources` collection.
* **ID:** `{url_hash}_{chunk_index}`
* **Document:** Plain text chunk content (~500 words).
* **Metadata:**
  * `source_url`: The URL the chunk was scraped from.
  * `title`: Page HTML title.
  * `chunk_index`: The sequential index of the chunk.
  * `ingested_at`: UTC ISO timestamp.

### Session Store (SQLite)
Stored at `backend/chroma_data/sessions.db` with relational constraints.
* **`sessions` Table:**
  * `id` (TEXT, PK): UUID.
  * `title` (TEXT): Conversation title.
  * `source_url` (TEXT, Nullable): Scopes the chat session to search only this URL if specified.
  * `created_at` (TEXT): ISO timestamp.
* **`messages` Table:**
  * `id` (INTEGER, PK): Auto-incrementing ID.
  * `session_id` (TEXT, FK): Links to the active session.
  * `role` (TEXT): `user` or `assistant`.
  * `content` (TEXT): The message text.
  * `citations` (TEXT, Nullable): JSON string array of citations containing `{url, snippet}`.
  * `created_at` (TEXT): ISO timestamp.

---

## API Reference

### Session Management

#### `GET /sessions`
Returns a list of all active conversations.
* **Response:** `200 OK` (JSON array of sessions)

#### `POST /sessions`
Creates a new conversation session.
* **Request Body:** `{ "title": "Chat Title", "source_url": "optional_url_to_scope_chat" }`
* **Response:** `200 OK` (created session details)

#### `GET /sessions/{session_id}/messages`
Retrieves full history of messages for a session.
* **Response:** `200 OK` (JSON array of messages with parsed citations)

#### `DELETE /sessions/{session_id}`
Deletes a session and cascadingly removes all of its messages.
* **Response:** `200 OK`

### Ingestion & Search

#### `POST /ingest`
Used by n8n to supply pre-scraped web text.
* **Request Body:** `{ "url": "...", "raw_text": "...", "title": "..." }`

#### `POST /ingest-url`
Fetches, cleans, and indexes the URL directly.
* **Request Body:** `{ "url": "..." }`

#### `POST /query`
Performs semantic retrieval, loads SQLite history, and generates a grounded response.
* **Request Body:** `{ "question": "...", "session_id": "optional-uuid", "top_k": 5 }`

#### `GET /sources`
Lists all unique ingested URLs, ingestion times, and total chunks.

#### `GET /provider`
Reports which LLM provider is active (Groq or Ollama) and details the currently selected model.

---

## Environment Variables

Configure these in `backend/.env` (a template is available in `backend/.env.example`):
```env
# LLM Providers
GROQ_API_KEY=gsk_...                  # Leave blank to force local Ollama execution
GROQ_MODEL=qwen/qwen3.6-27b           # Preferred cloud LLM model
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b              # Fallback local LLM model

# Embeddings
EMBEDDING_MODEL=nomic-embed-text:latest

# Storage Configuration
CHROMA_PERSIST_DIR=./chroma_data
CHROMA_COLLECTION_NAME=sources

# Parameters
TOP_K_RESULTS=5
SIMILARITY_THRESHOLD=0.35
CORS_ALLOWED_ORIGIN=http://localhost:5173

# LangSmith Tracing & Observability
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=lsv2_pt_...
LANGCHAIN_PROJECT=Research_Assistant_with_memory
```

---

## Setup & Run

### The Automated Way (Linux/macOS)
You can start all three applications simultaneously (FastAPI, React Dev Server, and Streamlit) with logs outputted to root-level log files:
```bash
# Start all services
./run.sh

# Monitor logs
tail -f backend.log frontend.log streamlit.log

# Stop all services
./stop.sh
```

### The Manual Way

#### 1. Setup Ollama
Make sure Ollama is installed and running, then pull the necessary models:
```bash
ollama pull nomic-embed-text:latest
ollama pull llama3.2:3b
```

#### 2. Run Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# Set up your .env file
uvicorn main:app --host 0.0.0.0 --port 8000
```

#### 3. Run React Frontend
```bash
cd frontend
npm install
npm run dev
```

#### 4. Run Streamlit UI
```bash
cd streamlit
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py --server.port 8501
```

---

## Design Decisions

1. **FastAPI Server-Side Orchestration:** Keeps database files, Chroma collections, and API keys securely in the backend. Frontends remain lightweight.
2. **SQLite relational persistence:** SQLite was selected for session and conversational tracking because of its zero-configuration local storage, simplicity, and transactional integrity.
3. **Similarity Cutoffs:** To prevent the LLM from hallucinating answers based on unrelated chunks, a similarity threshold of `0.35` is enforced. Chunks below this are ignored before the prompt reaches the LLM.
4. **Fallback & Robustness:** Cloud LLM (Groq) is used for speed and intelligence, but falls back to Ollama instantly on network timeouts, token limit failures, or rate-limiting error codes.
5. **Thinking Tag Stripping:** Modern reasoning models output internal thoughts within `<think>` tags. The backend detects and strips these blocks out before returning answers, keeping the chat clean.
6. **Ecosystem Observability (LangSmith):** Integrates standard tracing parameters to track pipeline performance, context chunk similarity, and model latencies in a unified observability dashboard.
7. **Timeout Prevention:** Disables request timeout boundaries for local Ollama invocation to guarantee that CPU-driven local inference completes without triggering network timeout exceptions.


---

## Known Limitations

1. **JS-heavy rendering:** Pages that build their DOM entirely through client-side JS will yield thin text when scraping directly. Setting up the n8n headless browser helper resolves this.
2. **GPU Availability:** Embedding and local inference speed is dependent on local GPU acceleration. If run on CPU alone, ingest and local Ollama queries can take significantly longer.
3. **Chunking Boundaries:** Word-based chunking can occasionally sever paragraphs or code blocks. Semantic chunking is planned for future releases.

---

## Roadmap

- [x] Persistent session history using SQLite.
- [x] Streamlit alternative web dashboard.
- [x] Automate starting and stopping dev environments (`run.sh`/`stop.sh`).
- [x] Automatic LLM provider failover.
- [x] Stripping of `<think>` reasoning blocks.
- [ ] Support direct document uploads (PDF, TXT, DOCX) in both UIs.
- [ ] Add streaming responses from LLM endpoints.
- [ ] Implement user authentication and workspace isolation.
