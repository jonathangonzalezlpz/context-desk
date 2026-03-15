from enum import Enum
from pydantic import BaseModel, Field
from typing import List, Optional

class Role(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class Message(BaseModel):
    role: Role
    content: str

class ChatSession(BaseModel):
    session_id: str
    messages: List[Message] = Field(default_factory=list)

class IntentType(str, Enum):
    FAQ = "faq"
    CATALOG = "catalog"
    GREETING = "greeting"
    DOMAIN_PROHIBITED = "domain_prohibited"
    UNKNOWN = "unknown"

class ChatRequest(BaseModel):
    session_id: str
    message: str

class ChatResponse(BaseModel):
    session_id: str
    message: str
    intent: Optional[IntentType] = None
    is_blocked: bool = False
