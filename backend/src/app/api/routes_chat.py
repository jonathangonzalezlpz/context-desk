from fastapi import APIRouter, Depends
from backend.src.app.domain.chat.models import ChatRequest, ChatResponse
from backend.src.app.platform.orchestrator import ChatOrchestrator
from backend.src.app.api.dependencies import get_chat_orchestrator

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(
    request: ChatRequest,
    orchestrator: ChatOrchestrator = Depends(get_chat_orchestrator)
) -> ChatResponse:
    """
    Principal Web Endpoint for the Chatbot.
    Delegates all logic to the Orchestrator.
    """
    response = orchestrator.process_message(request.session_id, request.message)
    return response

