import os
from backend.src.app.domain.chat.models import IntentType, ChatResponse
from backend.src.app.platform.guardrails.service import GuardrailService
from backend.src.app.platform.rag.service import RagService
from backend.src.app.infrastructure.repositories.catalog import CatalogRepository
from langchain_core.messages import SystemMessage, HumanMessage

class ChatOrchestrator:
    """
    Core Application Use Case.
    Coordinates Guardrails, RAG, Catalog and LLM.
    """
    def __init__(
        self,
        guardrail_service: GuardrailService,
        rag_service: RagService,
        catalog_repository: CatalogRepository
    ):
        self.guardrails = guardrail_service
        self.rag = rag_service
        self.catalog = catalog_repository
        
        # Determine LLM Provider from env (defaulting to Mock if no keys)
        api_key = os.environ.get("GROQ_API_KEY") or os.environ.get("OPENAI_API_KEY")
        
        if os.environ.get("GROQ_API_KEY"):
            from langchain_groq import ChatGroq
            self.llm = ChatGroq(temperature=0.0, model_name="llama3-8b-8192")
            print("🤖 Using Groq (Llama 3) as LLM Provider")
        elif os.environ.get("OPENAI_API_KEY"):
            from langchain_openai import ChatOpenAI
            self.llm = ChatOpenAI(temperature=0.0, model="gpt-4o-mini")
            print("🤖 Using OpenAI as LLM Provider")
        else:
            self.llm = None
            print("⚠️  No LLM API Key found. Chat will run in 'Mock' mode.")

    def process_message(self, session_id: str, user_message: str) -> ChatResponse:
        # 1. Hard Guardrail Check
        is_safe, reason = self.guardrails.is_safe_message(user_message)
        if not is_safe:
            return ChatResponse(
                session_id=session_id,
                message=self.guardrails.get_blocked_response(),
                intent=IntentType.DOMAIN_PROHIBITED,
                is_blocked=True
            )

        # 2. Intent Classification
        intent = self.guardrails.classify_intent_heuristic(user_message)
        
        # 3. Context Construction
        system_context = (
            "Eres un asistente virtual para una farmacia. "
            "Responde de forma concisa, amable y profesional. "
            "IMPORTANTE: No ofrezcas medicamentos ni consejos de salud bajo ningún concepto.\n\n"
        )
        
        # Catalog Logic
        if any(word in user_message.lower() for word in ["comprar", "tienen", "precio", "cuanto cuesta", "champú", "crema"]):
            products = self.catalog.search_products(user_message)
            if products:
                catalog_context = "Productos encontrados en el catálogo estructurado:\n"
                for p in products:
                    stock_msg = "En stock" if p.in_stock else "Agotado"
                    catalog_context += f"- {p.name} ({p.brand}): {p.price_cents / 100:.2f}€ - {stock_msg}\n"
                system_context += catalog_context
            else:
                system_context += "No se encontraron productos exactos en el catálogo estructurado.\n"
                
        # RAG Context (Local Embeddings)
        rag_context = self.rag.retrieve_context(user_message)
        system_context += f"Contexto de la base de conocimiento:\n{rag_context}"

        # 4. LLM Generation
        if self.llm:
            messages = [
                SystemMessage(content=system_context),
                HumanMessage(content=user_message)
            ]
            ai_msg = self.llm.invoke(messages)
            content = str(ai_msg.content)
        else:
            # Mock mode implementation if no LLM key is provided
            content = (
                "SISTEMA: No se ha configurado ninguna API Key (OpenAI/Groq). "
                "Este es un mensaje de prueba con el contexto recuperado:\n\n"
                f"{rag_context[:200]}..."
            )

        # 5. Output Guardrail
        is_safe_output, _ = self.guardrails.is_safe_message(content)
        if not is_safe_output:
            return ChatResponse(
                session_id=session_id,
                message=self.guardrails.get_blocked_response(),
                intent=IntentType.DOMAIN_PROHIBITED,
                is_blocked=True
            )

        return ChatResponse(
            session_id=session_id,
            message=content,
            intent=intent,
            is_blocked=False
        )
