from fastapi import FastAPI
from backend.src.app.api.routes_health import router as health_router
from backend.src.app.api.routes_chat import router as chat_router
from backend.src.app.core.config import settings

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version="0.1.0",
        description="Domain-safe chatbot API"
    )
    
    app.include_router(health_router, prefix="/api/v1")
    app.include_router(chat_router, prefix="/api/v1")
    return app

app = create_app()
