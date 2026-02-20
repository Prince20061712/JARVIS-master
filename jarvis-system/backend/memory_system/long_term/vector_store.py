import os
from typing import List, Dict, Any, Optional
import uuid

try:
    import chromadb
    from chromadb.config import Settings
except ImportError:
    chromadb = None
    print("⚠️ ChromaDB module not found. VectorStore will be disabled.")

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None
    print("⚠️ sentence-transformers module not found. VectorStore embeddings will fail.")

from utils.logger import logger

class VectorStore:
    """
    Manages vector embeddings using ChromaDB for long-term semantic memory.
    """
    def __init__(self, persist_directory: str = "data/processed/embeddings"):
        self.persist_directory = persist_directory
        self.client = None
        self.embedding_model = None
        
        self._initialize_db()

    def _initialize_db(self):
        if not chromadb or not SentenceTransformer:
            logger.error("VectorStore dependencies missing.")
            return
            
        try:
            os.makedirs(self.persist_directory, exist_ok=True)
            self.client = chromadb.PersistentClient(path=self.persist_directory)
            logger.info(f"ChromaDB initialized at {self.persist_directory}")
            
            # Use a lightweight fast embedding model
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("SentenceTransformer model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize VectorStore: {e}")

    def create_collection(self, name: str) -> bool:
        """Create or get an existing collection."""
        if not self.client: return False
        try:
            self.client.get_or_create_collection(name=name)
            logger.debug(f"Collection '{name}' ready.")
            return True
        except Exception as e:
            logger.error(f"Error creating collection {name}: {e}")
            return False

    def list_collections(self) -> List[str]:
        if not self.client: return []
        return [c.name for c in self.client.list_collections()]

    def delete_collection(self, name: str) -> bool:
        if not self.client: return False
        try:
            self.client.delete_collection(name=name)
            logger.info(f"Deleted collection '{name}'")
            return True
        except Exception as e:
            logger.error(f"Error deleting collection {name}: {e}")
            return False

    def add_documents(self, collection_name: str, texts: List[str], metadatas: Optional[List[Dict[str, Any]]] = None, ids: Optional[List[str]] = None) -> bool:
        """Batch add documents with embeddings into a specific collection."""
        if not self.client or not self.embedding_model: return False
        
        try:
            collection = self.client.get_or_create_collection(name=collection_name)
            if not ids:
                ids = [str(uuid.uuid4()) for _ in range(len(texts))]
            if not metadatas:
                metadatas = [{} for _ in range(len(texts))]
                
            # Generate Embeddings (Batch)
            embeddings = self.embedding_model.encode(texts).tolist()
            
            collection.add(
                documents=texts,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )
            logger.info(f"Added {len(texts)} documents to '{collection_name}'")
            return True
        except Exception as e:
            logger.error(f"Failed to add documents to {collection_name}: {e}")
            return False

    def similarity_search(self, collection_name: str, query: str, n_results: int = 4, where_filter: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Search similar context vectors."""
        if not self.client or not self.embedding_model: return []
        
        try:
            collection = self.client.get_collection(name=collection_name)
            query_embedding = self.embedding_model.encode([query]).tolist()
            
            results = collection.query(
                query_embeddings=query_embedding,
                n_results=n_results,
                where=where_filter
            )
            
            formatted_results = []
            if results['documents']:
                for i in range(len(results['documents'][0])):
                    formatted_results.append({
                        "id": results['ids'][0][i] if 'ids' in results else None,
                        "document": results['documents'][0][i],
                        "metadata": results['metadatas'][0][i] if 'metadatas' in results else {},
                        "distance": results['distances'][0][i] if 'distances' in results else None
                    })
            return formatted_results
        except Exception as e:
            logger.error(f"Search failed on collection '{collection_name}': {e}")
            return []

    def delete_documents(self, collection_name: str, ids: List[str]) -> bool:
        """Delete specific documents by IDs."""
        if not self.client: return False
        try:
            collection = self.client.get_collection(name=collection_name)
            collection.delete(ids=ids)
            logger.info(f"Deleted {len(ids)} documents from {collection_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete documents: {e}")
            return False
