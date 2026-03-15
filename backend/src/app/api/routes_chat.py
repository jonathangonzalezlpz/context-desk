from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from backend.src.app.domain.chat.models import ChatRequest, ChatResponse
from backend.src.app.platform.orchestrator import ChatOrchestrator
from backend.src.app.api.dependencies import get_chat_orchestrator

router = APIRouter()

@router.post("/chat")
def chat_endpoint(
    request: ChatRequest,
    orchestrator: ChatOrchestrator = Depends(get_chat_orchestrator)
):
    """
    Principal Web Endpoint for the Chatbot.
    Returns a stream of tokens for better UX.
    """
    return StreamingResponse(
        orchestrator.stream_message(request.session_id, request.message),
        media_type="text/plain"
    )

