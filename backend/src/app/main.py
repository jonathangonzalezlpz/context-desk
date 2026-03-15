from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.src.app.api.routes_health import router as health_router
from backend.src.app.api.routes_chat import router as chat_router
from backend.src.app.core.config import settings
from backend.src.app.infrastructure.database.session import engine, Base
# Import models so they are registered with Base metadata
from backend.src.app.infrastructure.database import models 

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version="0.1.0",
        description="Domain-safe chatbot API"
    )
    
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    app.include_router(health_router, prefix="/api/v1")
    app.include_router(chat_router, prefix="/api/v1")
    return app

app = create_app()
