from qdrant_client import QdrantClient
from langchain_community.vectorstores import Qdrant
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings

class RagService:
    def __init__(self, client: QdrantClient):
        self.client = client
        self.collection_name = "knowledge_base"
        
        # Free local embeddings (FastEmbed)
        self.embeddings = FastEmbedEmbeddings(model_name="BAAI/bge-small-en-v1.5")
        
        # Setup Langchain to query the existing Qdrant collection using the local model
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
            # We filter by domain_id in the search if needed (future multitenancy)
            docs = self.vector_store.similarity_search(query, k=k)
            return "\n\n".join([doc.page_content for doc in docs])
        except Exception as e:
            return f"No se pudo recuperar información adicional. (Error: {str(e)})"
