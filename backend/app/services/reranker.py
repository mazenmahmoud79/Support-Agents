"""
Re-ranking service using Cross-Encoder for improved retrieval accuracy.
"""
import asyncio
from typing import List, Dict, Any
from sentence_transformers import CrossEncoder
from app.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class RerankerService:
    """Service for re-ranking retrieved chunks using Cross-Encoder."""
    
    def __init__(self):
        """Initialize re-ranker with lazy loading."""
        self._model = None
        self._model_lock = asyncio.Lock()
        self.model_name = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    
    async def _get_model(self) -> CrossEncoder:
        """Lazy load the cross-encoder model."""
        if self._model is None:
            async with self._model_lock:
                if self._model is None:  # Double-check
                    logger.info(f"Loading cross-encoder model: {self.model_name}")
                    loop = asyncio.get_event_loop()
                    self._model = await loop.run_in_executor(
                        None,
                        lambda: CrossEncoder(self.model_name, max_length=512)
                    )
                    logger.info("Cross-encoder model loaded successfully")
        return self._model
    
    async def rerank(
        self,
        query: str,
        chunks: List[Dict[str, Any]],
        top_k: int = None
    ) -> List[Dict[str, Any]]:
        """
        Re-rank chunks based on their relevance to the query.
        
        Args:
            query: User's query
            chunks: List of retrieved chunks with metadata
            top_k: Number of top chunks to return (None = return all)
        
        Returns:
            List of re-ranked chunks with 'rerank_score' added
        """
        if not chunks:
            return chunks
        
        logger.info(f"Re-ranking {len(chunks)} chunks")
        
        # Get model
        model = await self._get_model()
        
        # Prepare query-chunk pairs
        pairs = [[query, chunk['text']] for chunk in chunks]
        
        # Run re-ranking in executor to avoid blocking
        loop = asyncio.get_event_loop()
        scores = await loop.run_in_executor(
            None,
            lambda: model.predict(pairs, show_progress_bar=False)
        )
        
        # Add re-rank scores to chunks
        for chunk, score in zip(chunks, scores):
            chunk['rerank_score'] = float(score)
            # Keep original vector similarity score as well
            chunk['vector_score'] = chunk.get('score', 0.0)
        
        # Sort by re-rank score (descending)
        reranked = sorted(chunks, key=lambda x: x['rerank_score'], reverse=True)
        
        # Log score changes
        if len(reranked) > 0:
            top_chunk = reranked[0]
            logger.info(
                f"Top chunk after re-ranking: {top_chunk['filename'][:30]} "
                f"(Vector: {top_chunk['vector_score']:.3f}, Rerank: {top_chunk['rerank_score']:.3f})"
            )
        
        # Return top_k if specified
        if top_k:
            reranked = reranked[:top_k]
            logger.info(f"Returning top {top_k} re-ranked chunks")
        
        return reranked


# Global instance
_reranker_service = None


def get_reranker_service() -> RerankerService:
    """Get or create the global reranker service instance."""
    global _reranker_service
    if _reranker_service is None:
        _reranker_service = RerankerService()
    return _reranker_service
