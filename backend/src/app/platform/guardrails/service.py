import re
import difflib
import numpy as np
from typing import Tuple, Optional, Pattern
from backend.src.app.domain.chat.models import IntentType

class GuardrailService:
    def __init__(self, blocked_terms: list[str], blocked_response: str, semantic_phrases: Optional[list[str]] = None):
        self.blocked_terms = [t.lower() for t in blocked_terms]
        self.blocked_response = blocked_response
        self.semantic_phrases = semantic_phrases or []
        
        self.blocked_regex: Optional[Pattern[str]] = None
        if self.blocked_terms:
            escaped_terms = [re.escape(t) for t in self.blocked_terms]
            pattern = r'\b(?:' + '|'.join(escaped_terms) + r')\b'
            self.blocked_regex = re.compile(pattern, re.IGNORECASE)

        self.embeddings = None
        self.semantic_vectors = None
        if self.semantic_phrases:
            try:
                from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
                print("⚡ GuardrailService: Initializing FastEmbed for semantic guardrails...")
                self.embeddings = FastEmbedEmbeddings(model_name="BAAI/bge-small-en-v1.5")
                self.semantic_vectors = np.array(self.embeddings.embed_documents(self.semantic_phrases))
            except ImportError as e:
                print(f"⚠️ Warning: Could not initialize FastEmbed for semantic guardrails: {e}")
            except Exception as e:
                print(f"⚠️ Warning: FastEmbed error: {e}")

    def is_safe_message(self, text: str) -> Tuple[bool, str]:
        """
        Validates if the message contains prohibited intent utilizing 3 layers:
        1. Exact Regex Match
        2. Fuzzy Word match (prevent typos/evasion)
        3. Semantic Cosine Similarity via FastEmbed (Intent classification)
        """
        if self.blocked_regex:
            match = self.blocked_regex.search(text)
            if match:
                return False, f"Término prohibido detectado: {match.group()}"
                
        words = re.findall(r'\b[a-zA-Z0-9_\-]+\b', text.lower())
        for word in words:
            if len(word) > 4:
                matches = difflib.get_close_matches(word, self.blocked_terms, n=1, cutoff=0.85)
                if matches:
                    return False, f"Variación de término prohibido: {matches[0]} (encontrado: {word})"

        if getattr(self, "semantic_vectors", None) is not None and self.embeddings is not None:
            try:
                query_vector = np.array(self.embeddings.embed_query(text))
                q_norm = np.linalg.norm(query_vector)
                
                if q_norm > 0:
                    for i, ref_vector in enumerate(self.semantic_vectors):
                        r_norm = np.linalg.norm(ref_vector)
                        if r_norm == 0:
                            continue
                        sim = np.dot(query_vector, ref_vector) / (q_norm * r_norm)
                        if sim > 0.82: 
                            return False, f"Intención prohibida detectada (símil a: '{self.semantic_phrases[i]}')"
            except Exception as e:
                print(f"⚠️ Semantic check failed (ignored for latency preservation): {e}")

        return True, ""

    def get_blocked_response(self) -> str:
        """Standardized response for blocked domain questions."""
        return self.blocked_response

    def classify_intent_heuristic(self, text: str) -> IntentType:
        """
        A very fast heuristic to classify intents before hitting LLM.
        Can be expanded.
        """
        is_safe, _ = self.is_safe_message(text)
        if not is_safe:
            return IntentType.DOMAIN_PROHIBITED
            
        text_lower = text.lower()
        if any(greet in text_lower for greet in ["hola", "buenos dias", "olá", "hello"]):
            # This is naive. In a real system we use an LLM router or a small classifier text model.
            pass
            
        return IntentType.UNKNOWN
