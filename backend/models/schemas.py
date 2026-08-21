from pydantic import BaseModel


class IngestRequest(BaseModel):
    url: str
    raw_text: str
    title: str = ""


class IngestResponse(BaseModel):
    status: str
    chunks_added: int
    url: str


class QueryRequest(BaseModel):
    question: str
    top_k: int = 5
    session_id: str | None = None


class Citation(BaseModel):
    url: str
    snippet: str


class QueryResponse(BaseModel):
    answer: str
    citations: list[Citation]
    found_in_sources: bool
    provider: str | None = None


class SourceItem(BaseModel):
    url: str
    ingested_at: str
    chunk_count: int


class SourcesResponse(BaseModel):
    sources: list[SourceItem]


class ExportRequest(BaseModel):
    session_history: list[dict]


class SessionCreate(BaseModel):
    title: str
    source_url: str | None = None


class SessionResponse(BaseModel):
    id: str
    title: str
    source_url: str | None
    created_at: str


class MessageResponse(BaseModel):
    id: int
    session_id: str
    role: str
    content: str
    citations: list[Citation]
    created_at: str

