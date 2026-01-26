"""
Embedding generation service using sentence-transformers.
"""
import asyncio
from typing import List, Dict, Any
from functools import lru_cache
import numpy as np
from sentence_transformers import SentenceTransformer
from app.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class EmbeddingService:
    """Service for generating text embeddings."""
    
    def __init__(self):
        """Initialize the embedding service."""
        self.model = None
        self._model_lock = asyncio.Lock()
    
    async def _load_model(self):
        """Load the sentence transformer model (lazy loading)."""
        if self.model is None:
            async with self._model_lock:
                if self.model is None:  # Double-check
                    logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
                    # Load model in thread pool to avoid blocking
                    loop = asyncio.get_event_loop()
                    self.model = await loop.run_in_executor(
                        None,
                        SentenceTransformer,
                        settings.EMBEDDING_MODEL
                    )
                    logger.info("Embedding model loaded successfully")
    
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Input text
        
        Returns:
            List[float]: Embedding vector
        """
        await self._load_model()
        
        # Generate embedding in thread pool
        loop = asyncio.get_event_loop()
        embedding = await loop.run_in_executor(
            None,
            self.model.encode,
            text
        )
        
        return embedding.tolist()
    
    async def generate_embeddings_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batches.
        
        Args:
            texts: List of input texts
            batch_size: Batch size for processing
        
        Returns:
            List[List[float]]: List of embedding vectors
        """
        await self._load_model()
        
        logger.info(f"Generating embeddings for {len(texts)} texts")
        
        # Generate embeddings in thread pool with batching
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(
            None,
            lambda: self.model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=len(texts) > 100,
                convert_to_numpy=True
            )
        )
        
        # Convert to list of lists
        return embeddings.tolist()
    
    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of the embedding vectors.
        
        Returns:
            int: Embedding dimension
        """
        return settings.EMBEDDING_DIMENSION


# Global embedding service instance
_embedding_service: EmbeddingService = None


def get_embedding_service() -> EmbeddingService:
    """
    Get the global embedding service instance.
    
    Returns:
        EmbeddingService: Embedding service
    """
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
