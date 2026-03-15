import pytest
from backend.src.app.platform.guardrails.service import GuardrailService
from backend.src.app.domain.chat.models import IntentType

@pytest.fixture
def guardrails():
    terms = [
        "paracetamol", "ibuprofeno", "fiebre", "tos", "infeccion", "embarazada", 
        "dosis", "niño", "recomiendas"
    ]
    response = "Blockeado por test"
    return GuardrailService(blocked_terms=terms, blocked_response=response)

def test_safe_messages(guardrails: GuardrailService):
    safe_texts = [
        "hola, a que hora abren?",
        "tienen champú anticaída?",
        "donde estan ubicados?",
        "necesito comprar crema hidratante",
        "cuarenta y cinco euros esta bien"
    ]
    for text in safe_texts:
        is_safe, reason = guardrails.is_safe_message(text)
        assert is_safe is True
        assert reason == ""

def test_blocked_clinical_terms(guardrails: GuardrailService):
    blocked_texts = [
        "hola, tienen paracetamol?",
        "cual es la dosis de ibuprofeno para un niño?",
        "estoy embarazada, puedo usar esto?",
        "tengo mucha tos y fiebre",
        "que me recomiendas para la infeccion?"
    ]
    for text in blocked_texts:
        is_safe, reason = guardrails.is_safe_message(text)
        assert is_safe is False
        assert "Término prohibido detectado" in reason

def test_heuristic_classification(guardrails: GuardrailService):
    assert guardrails.classify_intent_heuristic("quiero comprar paracetamol") == IntentType.DOMAIN_PROHIBITED
    assert guardrails.classify_intent_heuristic("hola, buenas tardes") == IntentType.UNKNOWN
