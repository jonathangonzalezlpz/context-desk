from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from backend.src.app.infrastructure.database.session import Base

class ProductModel(Base):
    """
    SQLAlchemy Model for the structured catalog database.
    This bypasses RAG and handles direct queries for stock/price.
    """
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    category = Column(String, index=True, nullable=False)
    brand = Column(String, index=True, nullable=True)
    description = Column(String, nullable=True)
    price_cents = Column(Integer, nullable=False)
    in_stock = Column(Boolean, default=True, nullable=False)

class ChatMessageModel(Base):
    """
    SQLAlchemy Model for persisting chat history.
    """
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True, nullable=False)
    role = Column(String, nullable=False) # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
