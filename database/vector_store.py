"""FAISS vector store for semantic search."""

import numpy as np
from typing import List, Dict, Any, Optional
from pathlib import Path
import json
import pickle


try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False


class VectorStore:
    """
    Manages FAISS vector store for semantic search over research content.
    """
    
    def __init__(self, dimension: int = 1536, index_path: Optional[Path] = None):
        """
        Initialize vector store.
        
        Args:
            dimension: Vector dimension (1536 for OpenAI embeddings)
            index_path: Path to save/load index
        """
        
        if not FAISS_AVAILABLE:
            raise ImportError("FAISS not available. Install with: pip install faiss-cpu")
            
        self.dimension = dimension
        self.index_path = index_path
        
        # Initialize FAISS index
        self.index = faiss.IndexFlatL2(dimension)
        
        # Store metadata for each vector
        self.metadata = []
        
        # Load existing index if available
        if index_path and index_path.exists():
            self.load()
            
    def add_vectors(
        self,
        vectors: np.ndarray,
        metadata: List[Dict[str, Any]]
    ):
        """
        Add vectors to the index.
        
        Args:
            vectors: Numpy array of shape (n, dimension)
            metadata: List of metadata dicts for each vector
        """
        
        if vectors.shape[1] != self.dimension:
            raise ValueError(f"Vector dimension mismatch: {vectors.shape[1]} != {self.dimension}")
            
        self.index.add(vectors)
        self.metadata.extend(metadata)
        
    def search(
        self,
        query_vector: np.ndarray,
        k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors.
        
        Args:
            query_vector: Query vector of shape (1, dimension)
            k: Number of results to return
            
        Returns:
            List of results with metadata and distances
        """
        
        if query_vector.shape[0] != 1:
            query_vector = query_vector.reshape(1, -1)
            
        distances, indices = self.index.search(query_vector, k)
        
        results = []
        for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
            if idx < len(self.metadata):
                result = {
                    "rank": i + 1,
                    "distance": float(dist),
                    "similarity": float(1 / (1 + dist)),  # Convert to similarity score
                    **self.metadata[idx]
                }
                results.append(result)
                
        return results
        
    def save(self):
        """Save index and metadata to disk."""
        
        if not self.index_path:
            raise ValueError("No index path specified")
            
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save FAISS index
        index_file = str(self.index_path) + ".index"
        faiss.write_index(self.index, index_file)
        
        # Save metadata
        metadata_file = str(self.index_path) + ".meta"
        with open(metadata_file, 'wb') as f:
            pickle.dump(self.metadata, f)
            
    def load(self):
        """Load index and metadata from disk."""
        
        if not self.index_path:
            raise ValueError("No index path specified")
            
        index_file = str(self.index_path) + ".index"
        metadata_file = str(self.index_path) + ".meta"
        
        if Path(index_file).exists():
            self.index = faiss.read_index(index_file)
            
        if Path(metadata_file).exists():
            with open(metadata_file, 'rb') as f:
                self.metadata = pickle.load(f)
                
    def clear(self):
        """Clear the index and metadata."""
        
        self.index.reset()
        self.metadata = []
        
    def size(self) -> int:
        """Get number of vectors in index."""
        
        return self.index.ntotal


class ResearchVectorStore:
    """
    Specialized vector store for research content.
    """
    
    def __init__(self, llm_client, index_path: Optional[Path] = None):
        """
        Initialize research vector store.
        
        Args:
            llm_client: OpenAI client for generating embeddings
            index_path: Path to save/load index
        """
        
        self.llm_client = llm_client
        self.store = VectorStore(dimension=1536, index_path=index_path)
        
    async def add_summaries(self, summaries: List[Dict[str, Any]]):
        """
        Add research summaries to vector store.
        
        Args:
            summaries: List of summary dictionaries
        """
        
        if not summaries:
            return
            
        # Prepare texts for embedding
        texts = []
        metadata = []
        
        for summary in summaries:
            text = f"{summary.get('title', '')}\n{summary.get('summary', '')}"
            texts.append(text)
            
            metadata.append({
                "url": summary.get("url", ""),
                "title": summary.get("title", ""),
                "summary": summary.get("summary", "")[:200]
            })
            
        # Generate embeddings
        embeddings = await self._get_embeddings(texts)
        
        # Add to store
        self.store.add_vectors(embeddings, metadata)
        
    async def search_similar(
        self,
        query: str,
        k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for similar content.
        
        Args:
            query: Search query
            k: Number of results
            
        Returns:
            List of similar items
        """
        
        # Generate query embedding
        query_embedding = await self._get_embeddings([query])
        
        # Search
        results = self.store.search(query_embedding, k)
        
        return results
        
    async def _get_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Get embeddings from OpenAI.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            Numpy array of embeddings
        """
        
        response = await self.llm_client.embeddings.create(
            model="text-embedding-3-small",
            input=texts
        )
        
        embeddings = np.array([
            item.embedding for item in response.data
        ], dtype=np.float32)
        
        return embeddings
        
    def save(self):
        """Save vector store."""
        self.store.save()
        
    def load(self):
        """Load vector store."""
        self.store.load()
