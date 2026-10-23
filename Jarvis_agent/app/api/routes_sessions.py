from typing import List
from fastapi import APIRouter, HTTPException, Path
from app.schemas.api import SessionSummary, SessionDetail
from app.memory.store import memory_store
from app.core.exceptions import SessionNotFoundError

router = APIRouter(prefix="/api/sessions", tags=["Sessions"])


@router.get("", response_model=List[SessionSummary], summary="List all conversation sessions")
async def list_sessions() -> List[SessionSummary]:
    return memory_store.list_sessions()


@router.get("/{session_id}/messages", response_model=SessionDetail, summary="Get full session messages")
async def get_session_messages(
    session_id: str = Path(..., description="UUID of session")
) -> SessionDetail:
    detail = memory_store.get_session_detail(session_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Session not found.")
    return detail


@router.delete("/{session_id}", summary="Delete conversation session")
async def delete_session(
    session_id: str = Path(..., description="UUID of session to delete")
):
    deleted = memory_store.delete_session(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found.")
    return {"status": "success", "message": f"Session '{session_id}' deleted."}
