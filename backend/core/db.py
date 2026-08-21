import sqlite3
import os
import json
from datetime import datetime, timezone
import uuid

DB_PATH = os.path.join(os.getenv("CHROMA_PERSIST_DIR", "./chroma_data"), "sessions.db")

def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            source_url TEXT,
            created_at TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            citations TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
        )
    """)
    conn.commit()
    conn.close()

def create_session(title: str, source_url: str = None) -> dict:
    conn = get_connection()
    cursor = conn.cursor()
    session_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat()
    cursor.execute(
        "INSERT INTO sessions (id, title, source_url, created_at) VALUES (?, ?, ?, ?)",
        (session_id, title, source_url, created_at)
    )
    conn.commit()
    conn.close()
    return {
        "id": session_id,
        "title": title,
        "source_url": source_url,
        "created_at": created_at
    }

def get_session(session_id: str) -> dict:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def list_sessions() -> list[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sessions ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_session_messages(session_id: str) -> list[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM messages WHERE session_id = ? ORDER BY id ASC", (session_id,))
    rows = cursor.fetchall()
    conn.close()
    messages = []
    for r in rows:
        m = dict(r)
        if m["citations"]:
            try:
                m["citations"] = json.loads(m["citations"])
            except Exception:
                m["citations"] = []
        else:
            m["citations"] = []
        messages.append(m)
    return messages

def add_message(session_id: str, role: str, content: str, citations: list = None) -> dict:
    conn = get_connection()
    cursor = conn.cursor()
    created_at = datetime.now(timezone.utc).isoformat()
    citations_str = json.dumps(citations) if citations is not None else None
    cursor.execute(
        "INSERT INTO messages (session_id, role, content, citations, created_at) VALUES (?, ?, ?, ?, ?)",
        (session_id, role, content, citations_str, created_at)
    )
    conn.commit()
    conn.close()
    return {
        "session_id": session_id,
        "role": role,
        "content": content,
        "citations": citations if citations is not None else [],
        "created_at": created_at
    }

def delete_session(session_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")
    cursor.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
    cursor.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
    conn.commit()
    conn.close()
