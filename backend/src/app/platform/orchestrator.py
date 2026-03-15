import os
from backend.src.app.domain.chat.models import IntentType, ChatResponse
from backend.src.app.platform.guardrails.service import GuardrailService
from backend.src.app.platform.rag.service import RagService
from backend.src.app.infrastructure.repositories.catalog import CatalogRepository
from backend.src.app.infrastructure.database.models import ChatMessageModel
from sqlalchemy.orm import Session
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

class ChatOrchestrator:
    """
    Core Application Use Case.
    Coordinates Guardrails, RAG, Catalog and LLM.
    """
    def __init__(
        self,
        guardrail_service: GuardrailService,
        rag_service: RagService,
        catalog_repository: CatalogRepository,
        system_prompt: str = "Eres un asistente virtual servicial.",
        relevancy_config: dict = None
    ):
        self.guardrails = guardrail_service
        self.rag = rag_service
        self.catalog = catalog_repository
        self.db: Session = catalog_repository.db
        self.system_prompt = system_prompt
        self.relevancy_config = relevancy_config or {}
        
        # Determine LLM Provider from env (defaulting to Mock if no keys)
        provider = os.environ.get("PROVIDER_SELECTED", "").lower()
        
        if provider == "groq" and os.environ.get("GROQ_API_KEY"):
            from langchain_groq import ChatGroq
            self.llm = ChatGroq(temperature=0.0, model_name="llama3-8b-8192")
            print("🤖 Using Groq (Llama 3) as LLM Provider")
        elif provider == "openai" and os.environ.get("OPENAI_API_KEY"):
            from langchain_openai import ChatOpenAI
            self.llm = ChatOpenAI(temperature=0.0, model="gpt-4o-mini")
            print("🤖 Using OpenAI as LLM Provider")
        elif provider == "ollama":
            from langchain_ollama import ChatOllama
            base_url = os.environ.get("OLLAMA_BASE_URL", "http://ollama:11434")
            model = os.environ.get("OLLAMA_MODEL", "llama3")
            num_ctx = int(os.environ.get("OLLAMA_NUM_CTX", 4096))
            self.llm = ChatOllama(base_url=base_url, model=model, temperature=0.0, num_ctx=num_ctx)
            print(f"🤖 Using Ollama ({model}) context={num_ctx} as LLM Provider at {base_url}")
        else:
            # Auto-detection if no specific provider is forced
            if os.environ.get("GROQ_API_KEY"):
                from langchain_groq import ChatGroq
                self.llm = ChatGroq(temperature=0.0, model_name="llama3-8b-8192")
                print("🤖 Auto-detected: Using Groq")
            elif os.environ.get("OPENAI_API_KEY"):
                from langchain_openai import ChatOpenAI
                self.llm = ChatOpenAI(temperature=0.0, model="gpt-4o-mini")
                print("🤖 Auto-detected: Using OpenAI")
            else:
                self.llm = None
                print("⚠️  No LLM API Key or Provider found. Chat will run in 'Mock' mode.")

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
        
        # 3. Context Construction (Dynamic Prompt)
        system_context = self.system_prompt + "\n\n"
        
        # Catalog Logic (Dynamic from Config)
        catalog_keywords = self.relevancy_config.get("catalog_trigger_keywords", [])
        if any(word in user_message.lower() for word in catalog_keywords):
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
        
        # 3.5. Semantic Relevancy Check
        if not self.is_relevant_to_domain(user_message, system_context):
            return ChatResponse(
                session_id=session_id,
                message="Lo siento, solo puedo ayudarte con consultas relacionadas con la farmacia, salud general y nuestro catálogo de productos. No puedo responder sobre otros temas.",
                intent=intent,
                is_blocked=False
            )

        # 4. Load History & LLM Generation
        if self.llm:
            # Load last 10 messages for context
            history = self.db.query(ChatMessageModel).filter(
                ChatMessageModel.session_id == session_id
            ).order_by(ChatMessageModel.created_at.asc()).limit(10).all()
            
            messages = [SystemMessage(content=system_context)]
            for msg in history:
                if msg.role == "user":
                    messages.append(HumanMessage(content=msg.content))
                else:
                    messages.append(AIMessage(content=msg.content))
            
            messages.append(HumanMessage(content=user_message))
            
            ai_msg = self.llm.invoke(messages)
            content = str(ai_msg.content)
            
            # Save User and Assistant messages
            self.db.add(ChatMessageModel(session_id=session_id, role="user", content=user_message))
            self.db.add(ChatMessageModel(session_id=session_id, role="assistant", content=content))
            self.db.commit()
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

    def stream_message(self, session_id: str, user_message: str):
        """
        Generator for streaming tokens and persisting history.
        """
        try:
            # 1. Hard Guardrail Check
            is_safe, reason = self.guardrails.is_safe_message(user_message)
            if not is_safe:
                yield f"ERROR: {self.guardrails.get_blocked_response()}"
                return

            # 2. Intent Classification
            intent = self.guardrails.classify_intent_heuristic(user_message)
            
            # 3. Context Construction (Dynamic Prompt)
            system_context = self.system_prompt + "\n\n"
            
            # Catalog Logic (Dynamic from Config)
            catalog_keywords = self.relevancy_config.get("catalog_trigger_keywords", [])
            if any(word in user_message.lower() for word in catalog_keywords):
                products = self.catalog.search_products(user_message)
                if products:
                    catalog_context = "Productos encontrados en el catálogo estructurado:\n"
                    for p in products:
                        stock_msg = "En stock" if p.in_stock else "Agotado"
                        catalog_context += f"- {p.name} ({p.brand}): {p.price_cents / 100:.2f}€ - {stock_msg}\n"
                    system_context += catalog_context
                    
            rag_context = self.rag.retrieve_context(user_message)
            system_context += f"Contexto de la base de conocimiento:\n{rag_context}"

            # 3.5. Semantic Relevancy Check
            if not self.is_relevant_to_domain(user_message, system_context):
                yield "Lo siento, solo puedo ayudarte con consultas relacionadas con la farmacia, salud general y nuestro catálogo de productos. No puedo responder sobre otros temas."
                return

            # 4. LLM Generation with Streaming
            full_content = ""
            if self.llm:
                # Load last 10 messages for context (wrapped in try for DB robustness)
                history = []
                try:
                    history = self.db.query(ChatMessageModel).filter(
                        ChatMessageModel.session_id == session_id
                    ).order_by(ChatMessageModel.created_at.asc()).limit(10).all()
                except Exception as e:
                    print(f"⚠️ Error loading history (might be first run): {e}")

                messages = [SystemMessage(content=system_context)]
                for msg in history:
                    if msg.role == "user":
                        messages.append(HumanMessage(content=msg.content))
                    else:
                        messages.append(AIMessage(content=msg.content))
                messages.append(HumanMessage(content=user_message))
                
                for chunk in self.llm.stream(messages):
                    token = chunk.content
                    full_content += token
                    yield token
                
                # Save User and Assistant messages after stream completes
                try:
                    self.db.add(ChatMessageModel(session_id=session_id, role="user", content=user_message))
                    self.db.add(ChatMessageModel(session_id=session_id, role="assistant", content=full_content))
                    self.db.commit()
                except Exception as e:
                    print(f"⚠️ Error saving messages to history: {e}")
                    self.db.rollback()
            else:
                yield "MODO MOCK: Streaming no disponible sin LLM."
        except Exception as e:
            import traceback
            print(f"❌ CRITICAL ERROR in stream_message: {e}")
            traceback.print_exc()
            yield f"\n[Error técnico: {str(e)}]"

    def is_relevant_to_domain(self, user_message: str, context: str) -> bool:
        """
        Generic relevancy check using configuration.
        """
        prohibited = self.relevancy_config.get("prohibited_topics", [])
        min_words = self.relevancy_config.get("min_words_for_check", 0)
        
        message_lower = user_message.lower()
        
        # 1. Hard exclusions
        if any(topic.lower() in message_lower for topic in prohibited):
            return False
            
        # 2. Skip if too short (e.g. "Hola")
        if len(user_message.split()) < min_words:
            return True
            
        # 3. Fallback: Relevancy is true by default unless hard-blocked above
        # In the future, this can use required_context_keywords or a second LLM pass
        return True
