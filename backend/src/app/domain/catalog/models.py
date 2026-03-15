from pydantic import BaseModel
from typing import Optional

class Product(BaseModel):
    id: int
    name: str
    category: str
    brand: Optional[str] = None
    description: Optional[str] = None
    price_cents: int
    in_stock: bool
    
class Category(BaseModel):
    id: int
    name: str
