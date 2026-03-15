from qdrant_client import QdrantClient
from backend.src.app.core.config import settings

def get_qdrant_client() -> QdrantClient:
    """
    Returns a configured QdrantClient instance for vector search.
    """
    return QdrantClient(url=settings.QDRANT_URL)
