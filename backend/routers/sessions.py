from fastapi import APIRouter, HTTPException
from models.schemas import SessionCreate, SessionResponse, MessageResponse
from core import db

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", response_model=SessionResponse)
def create_session_endpoint(payload: SessionCreate):
    try:
        session = db.create_session(title=payload.title, source_url=payload.source_url)
        return session
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")


@router.get("", response_model=list[SessionResponse])
def list_sessions_endpoint():
    try:
        return db.list_sessions()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list sessions: {str(e)}")


@router.get("/{session_id}/messages", response_model=list[MessageResponse])
def get_session_messages_endpoint(session_id: str):
    session = db.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    try:
        return db.get_session_messages(session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve messages: {str(e)}")


@router.delete("/{session_id}")
def delete_session_endpoint(session_id: str):
    session = db.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    try:
        db.delete_session(session_id)
        return {"status": "success", "message": f"Session {session_id} deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete session: {str(e)}")
