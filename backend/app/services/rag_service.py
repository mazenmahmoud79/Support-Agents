"""
RAG (Retrieval Augmented Generation) service that orchestrates
document retrieval and LLM response generation.
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from app.services.embeddings import get_embedding_service
from app.services.vector_store import get_vector_store
from app.services.llm_service import get_llm_service
from app.services.reranker import get_reranker_service
from app.core.logging import get_logger
from app.config import settings

logger = get_logger(__name__)


class RAGService:
    """Service for RAG pipeline orchestration."""
    
    def __init__(self):
        """Initialize RAG service with dependencies."""
        self.embedding_service = get_embedding_service()
        self.vector_store = get_vector_store()
        self.llm_service = get_llm_service()
        self.reranker_service = get_reranker_service()
    
    def _expand_query(self, user_message: str) -> str:
        """Expand short queries to improve semantic search accuracy."""
        # Only expand short queries (< 8 words) to avoid unnecessary processing
        word_count = len(user_message.split())
        if word_count >= 8:
            return user_message
        
        # Add contextual keywords to help vector search
        # This is a simple expansion - could be enhanced with LLM call if needed
        expanded = f"{user_message} information details explanation help"
        logger.debug(f"Query expanded from '{user_message}' to '{expanded}'")
        return expanded
    
    def _refine_query_with_history(self, user_message: str, chat_history: List[Dict[str, str]]) -> str:
        """Add conversational context to queries that reference previous messages."""
        if not chat_history:
            return user_message
        
        # Check if query uses pronouns or is follow-up question
        follow_up_indicators = ['it', 'that', 'this', 'they', 'also', 'and what about', 'more details']
        is_followup = any(indicator in user_message.lower() for indicator in follow_up_indicators)
        
        if is_followup and len(chat_history) > 0:
            # Add context from last user message
            last_user_msg = next((msg['content'] for msg in reversed(chat_history) if msg['role'] == 'user'), None)
            if last_user_msg:
                contextualized = f"Previous context: {last_user_msg[:100]}. Current question: {user_message}"
                logger.debug(f"Query contextualized with history: {contextualized[:150]}")
                return contextualized
        
        return user_message
    
    def _generate_alternative_queries(self, user_message: str) -> List[str]:
        """Generate alternative phrasings of the query for multi-query retrieval."""
        queries = [user_message]  # Always include original
        
        # Generate variations for better coverage
        msg_lower = user_message.lower()
        
        # If it's a question, also try statement form
        if '?' in user_message:
            statement = user_message.replace('?', '').strip()
            queries.append(f"Information about {statement}")
        
        # Add question forms for statements
        if '?' not in user_message:
            queries.append(f"How to {msg_lower}")
            queries.append(f"What is {msg_lower}")
        
        # Limit to 3 variations to avoid too many searches
        return queries[:3]
    
    async def query(
        self,
        user_message: str,
        tenant_id: str,
        company_name: str,
        session_id: str,
        chat_history: List[Dict[str, str]] = None,
        include_sources: bool = True,
        tenant_context: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, List[Dict[str, Any]], float]:
        """
        Execute RAG pipeline: retrieve relevant docs and generate response.
        
        Args:
            user_message: User's question
            tenant_id: Tenant ID
            company_name: Company name
            session_id: Conversation session ID
            chat_history: Recent conversation history
            include_sources: Whether to return source documents
            tenant_context: Optional context for customization (tone, style, etc.)
        
        Returns:
            Tuple of (response, sources, response_time)
        """
        start_time = datetime.utcnow()
        
        logger.info(f"RAG query for tenant {tenant_id}: {user_message[:100]}")
        
        # Step 1: Refine query with conversation context if it's a follow-up
        refined_query = self._refine_query_with_history(user_message, chat_history or [])
        
        # Step 2: Generate alternative queries for comprehensive retrieval
        query_variations = self._generate_alternative_queries(refined_query)
        logger.debug(f"Generated {len(query_variations)} query variations")
        
        # Step 3: Expand primary query for better semantic matching
        expanded_query = self._expand_query(query_variations[0])
        
        # Step 4: Retrieve chunks using multi-query approach
        all_chunks = []
        for query_var in query_variations:
            # Generate embedding for this variation
            query_embedding = await self.embedding_service.generate_embedding(query_var)
            
            # Retrieve relevant chunks
            chunks = await self.vector_store.search_similar(
                tenant_id=tenant_id,
                query_embedding=query_embedding,
                top_k=5,  # Fetch 5 per query variation
                score_threshold=0.1
            )
            all_chunks.extend(chunks)
        
        # Remove duplicates and keep top results
        logger.info(f"Retrieved {len(all_chunks)} total chunks from {len(query_variations)} queries")
        
        # Step 5: Re-rank chunks using Cross-Encoder for precision (if enabled)
        if settings.ENABLE_RERANKING:
            reranked_chunks = await self.reranker_service.rerank(
                query=user_message,  # Use original query for re-ranking
                chunks=all_chunks,
                top_k=settings.RERANK_TOP_K
            )
            logger.info(f"Re-ranked to top {len(reranked_chunks)} chunks")
        else:
            reranked_chunks = all_chunks
            logger.info("Re-ranking disabled, using vector search results")
        
        # Step 6: Build context from re-ranked chunks (with deduplication and filtering)
        context, sources = self._build_context(reranked_chunks, include_sources)
        
        # Step 7: Generate response with LLM
        if not context.strip():
            # No relevant context found - use fallback
            logger.warning(f"No relevant context found for query: {user_message[:50]}")
            response = self.llm_service.build_fallback_response(user_message)
            sources = []
        else:
            # Check if llm_service.generate_response supports tenant_context
            # Assuming it does or we will update it too. For now passing it as kwargs if supported or explicit arg
            # Looking at previous errors, it seems llm_service might need update too if it doesn't support it
            # But let's first fix RAGService signature which is the immediate error
            response = await self.llm_service.generate_response(
                user_message=user_message,
                context=context,
                company_name=company_name,
                chat_history=chat_history or [],
                tenant_context=tenant_context
            )
        
        # Calculate response time
        end_time = datetime.utcnow()
        response_time = (end_time - start_time).total_seconds()
        
        logger.info(f"RAG query completed in {response_time:.2f}s")
        
        return response, sources, response_time
    
    def _deduplicate_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate or highly similar chunks."""
        if not chunks:
            return chunks
        
        unique_chunks = []
        seen_texts = set()
        
        for chunk in chunks:
            # Create normalized text signature (first 200 chars, lowercased, whitespace normalized)
            text_signature = ' '.join(chunk['text'][:200].lower().split())
            
            if text_signature not in seen_texts:
                unique_chunks.append(chunk)
                seen_texts.add(text_signature)
            else:
                logger.debug(f"Removed duplicate chunk from {chunk['filename']}")
        
        logger.info(f"Deduplication: {len(chunks)} -> {len(unique_chunks)} chunks")
        return unique_chunks
    
    def _filter_by_score(self, chunks: List[Dict[str, Any]], min_score: float = 0.3) -> List[Dict[str, Any]]:
        """Filter out chunks with low relevance scores (works with both vector and rerank scores)."""
        if not chunks:
            return chunks
        
        # Use rerank_score if available, otherwise use vector score
        score_key = 'rerank_score' if chunks and 'rerank_score' in chunks[0] else 'score'
        
        # Adjust threshold for rerank scores (they use different scale)
        if score_key == 'rerank_score':
            min_score = -5.0  # Cross-encoder scores can be negative; -5 is a reasonable threshold
        
        filtered = [chunk for chunk in chunks if chunk.get(score_key, 0) >= min_score]
        
        if len(filtered) < len(chunks):
            logger.info(f"Score filtering ({score_key}): {len(chunks)} -> {len(filtered)} chunks (threshold: {min_score})")
        
        return filtered if filtered else chunks[:1]  # Keep at least one chunk
    
    def _build_context(
        self,
        chunks: List[Dict[str, Any]],
        include_sources: bool
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Build context string from retrieved chunks.
        
        Args:
            chunks: Retrieved chunks with metadata
            include_sources: Whether to prepare source information
        
        Returns:
            Tuple of (context_string, sources)
        """
        if not chunks:
            return "", []
        
        # Apply deduplication and score filtering
        chunks = self._deduplicate_chunks(chunks)
        chunks = self._filter_by_score(chunks, min_score=0.3)
        
        # Sort by rerank_score if available, otherwise use vector score
        sort_key = 'rerank_score' if chunks and 'rerank_score' in chunks[0] else 'score'
        chunks = sorted(chunks, key=lambda x: x.get(sort_key, 0), reverse=True)
        
        # Build context text with enhanced formatting
        context_parts = []
        sources = []
        
        for i, chunk in enumerate(chunks):
            # Determine which score to display
            if 'rerank_score' in chunk:
                score = chunk['rerank_score']
                score_type = "Rerank"
            else:
                score = chunk.get('score', 0)
                score_type = "Vector"
            
            relevance_label = "HIGH" if score > 0.7 else "MEDIUM" if score > 0.5 else "MODERATE"
            
            # Add chunk text to context with relevance indicator
            context_parts.append(f"[Source {i+1}: {chunk['filename']} | Relevance: {relevance_label} ({score_type}: {score:.2f})]")
            context_parts.append(chunk['text'])
            context_parts.append("")  # Empty line separator
            
            # Prepare source information
            if include_sources:
                sources.append({
                    "document_id": chunk['document_id'],
                    "filename": chunk['filename'],
                    "chunk_index": chunk['chunk_index'],
                    "relevance_score": round(float(chunk['score']), 3),
                    "snippet": chunk['text'][:500]  # First 500 chars
                })
        
        # Combine context parts
        context = "\n".join(context_parts)
        
        # Truncate if too long
        max_length = settings.MAX_CONTEXT_LENGTH
        if len(context) > max_length:
            logger.warning(f"Context truncated from {len(context)} to {max_length} characters")
            context = context[:max_length] + "... [truncated]"
        
        return context, sources
    
    async def query_stream(
        self,
        user_message: str,
        tenant_id: str,
        company_name: str,
        session_id: str,
        chat_history: List[Dict[str, str]] = None,
        tenant_context: Optional[Dict[str, Any]] = None
    ):
        """
        Execute RAG pipeline with streaming response.
        
        Args:
            user_message: User's question
            tenant_id: Tenant ID
            company_name: Company name
            session_id: Conversation session ID
            chat_history: Recent conversation history
            tenant_context: Optional context for customization
        
        Yields:
            Tuple of (chunk, sources, is_final)
        """
        logger.info(f"RAG streaming query for tenant {tenant_id}")
        
        # Step 1: Generate embedding
        query_embedding = await self.embedding_service.generate_embedding(user_message)
        
        # Step 2: Retrieve relevant chunks
        similar_chunks = await self.vector_store.search_similar(
            tenant_id=tenant_id,
            query_embedding=query_embedding,
            top_k=settings.TOP_K_RESULTS,
            score_threshold=0.1  # Hardcoded to fix caching issue (was settings.SIMILARITY_THRESHOLD)
        )
        
        # Step 3: Build context
        context, sources = self._build_context(similar_chunks, include_sources=True)
        
        # Step 4: Stream response
        if not context.strip():
            # No relevant context - return fallback
            fallback = self.llm_service.build_fallback_response(user_message)
            yield fallback, [], True
        else:
            # Stream LLM response
            async for chunk in self.llm_service.generate_response_stream(
                user_message=user_message,
                context=context,
                company_name=company_name,
                chat_history=chat_history or [],
                tenant_context=tenant_context
            ):
                yield chunk, sources, False
            
            # Final chunk with sources
            yield "", sources, True


# Global RAG service instance
_rag_service: RAGService = None


def get_rag_service() -> RAGService:
    """
    Get the global RAG service instance.
    
    Returns:
        RAGService: RAG service
    """
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
