from sqlalchemy.orm import Session
from backend.src.app.infrastructure.database.models import ProductModel
from backend.src.app.domain.catalog.models import Product

class CatalogRepository:
    def __init__(self, db_session: Session):
        self.db = db_session

    def search_products(self, query: str) -> list[Product]:
        """
        Simple exact/like search for products in the catalog without using vector embeddings.
        This provides deterministic results for shop catalog.
        """
        sql_query = f"%{query}%"
        # Using ILIKE semantics (for sqlite compatibility falling back to simple like, but assume PG is being used)
        results = self.db.query(ProductModel).filter(
            ProductModel.name.ilike(sql_query) | ProductModel.category.ilike(sql_query)
        ).limit(10).all()
        
        return [
            Product(
                id=r.id,
                name=r.name,
                category=r.category,
                brand=r.brand,
                description=r.description,
                price_cents=r.price_cents,
                in_stock=r.in_stock
            ) for r in results
        ]
