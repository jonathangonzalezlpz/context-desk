import os
import json
from pathlib import Path

from fastapi import Depends
from sqlalchemy.orm import Session
from qdrant_client import QdrantClient

from backend.src.app.infrastructure.database.session import get_db
from backend.src.app.infrastructure.qdrant.client import get_qdrant_client
from backend.src.app.infrastructure.repositories.catalog import CatalogRepository
from backend.src.app.platform.guardrails.service import GuardrailService
from backend.src.app.platform.rag.service import RagService
from backend.src.app.platform.orchestrator import ChatOrchestrator

def get_catalog_repository(db: Session = Depends(get_db)) -> CatalogRepository:
    return CatalogRepository(db_session=db)

def get_guardrail_service() -> GuardrailService:
    # Load configuration dynamically for the specific domain
    domain_active = os.getenv("DOMAIN_ACTIVE", "farmacia_demo")
    config_path = Path(f"knowledge/processed/{domain_active}/domain_config.json")
    
    blocked_terms = []
    blocked_response = "Estoy programado para no responder a este tipo de consultas por seguridad."
    
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            guardrails_config = data.get("guardrails", {})
            blocked_terms = guardrails_config.get("blocked_terms", [])
            blocked_response = guardrails_config.get("blocked_response_message", blocked_response)
            
    return GuardrailService(
        blocked_terms=blocked_terms, 
        blocked_response=blocked_response
    )

def get_rag_service(qdrant_client: QdrantClient = Depends(get_qdrant_client)) -> RagService:
    return RagService(client=qdrant_client)

def get_chat_orchestrator(
    guardrail_service: GuardrailService = Depends(get_guardrail_service),
    rag_service: RagService = Depends(get_rag_service),
    catalog_repository: CatalogRepository = Depends(get_catalog_repository)
) -> ChatOrchestrator:
    return ChatOrchestrator(
        guardrail_service=guardrail_service,
        rag_service=rag_service,
        catalog_repository=catalog_repository
    )
