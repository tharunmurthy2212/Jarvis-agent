from fastapi import APIRouter, HTTPException
from app.schemas.api import ChatRequest, ChatResponse
from app.assistant.engine import assistant_engine
from app.core.logger import logger

router = APIRouter(prefix="/api", tags=["Chat"])


@router.post("/chat", response_model=ChatResponse, summary="Send message to JARVIS")
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Send a message to JARVIS with session continuity, tool execution, and document grounding.
    """
    try:
        response = await assistant_engine.process_chat(request)
        return response
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An internal error occurred while processing the chat request."
        )
