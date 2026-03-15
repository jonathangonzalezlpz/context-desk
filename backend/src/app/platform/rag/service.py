from qdrant_client import QdrantClient
from langchain_community.vectorstores import Qdrant
from langchain_openai import OpenAIEmbeddings

class RagService:
    def __init__(self, client: QdrantClient):
        self.client = client
        self.collection_name = "knowledge_base"
        self.embeddings = OpenAIEmbeddings()
        
        # We assume the collection might be already created by a data ingestion script.
        # This setup allows Langchain to query the existing Qdrant collection.
        self.vector_store = Qdrant(
            client=self.client,
            collection_name=self.collection_name,
            embeddings=self.embeddings,
        )

    def retrieve_context(self, query: str, k: int = 3) -> str:
        """
        Retrieves relevant context from the vector database using semantic search.
        """
        try:
            docs = self.vector_store.similarity_search(query, k=k)
            return "\n\n".join([doc.page_content for doc in docs])
        except Exception as e:
            # Handle case where Qdrant is completely offline or collection doesn't exist yet
            return f"No se pudo recuperar información adicional. (Error: {str(e)})"
