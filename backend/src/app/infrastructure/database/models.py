from sqlalchemy import Column, Integer, String, Boolean
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
