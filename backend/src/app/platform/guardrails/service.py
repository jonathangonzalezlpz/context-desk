import re
from typing import Tuple
from backend.src.app.domain.chat.models import IntentType

class GuardrailService:
    def __init__(self, blocked_terms: list[str], blocked_response: str):
        self.blocked_terms = blocked_terms
        self.blocked_response = blocked_response
        
        if self.blocked_terms:
            # Compile regex for fast matching (case-insensitive, word boundaries)
            pattern = r'\b(?:' + '|'.join(map(re.escape, self.blocked_terms)) + r')\b'
            self.blocked_regex = re.compile(pattern, re.IGNORECASE)
        else:
            self.blocked_regex = None

    def is_safe_message(self, text: str) -> Tuple[bool, str]:
        """
        Validates if the message contains prohibited terms.
        Returns: (is_safe, optional_reason)
        """
        if not self.blocked_regex:
            return True, ""
            
        match = self.blocked_regex.search(text)
        if match:
            return False, f"Término prohibido detectado: {match.group()}"
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
