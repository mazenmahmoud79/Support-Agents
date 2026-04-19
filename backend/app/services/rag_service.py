"""
RAG (Retrieval Augmented Generation) service that orchestrates
document retrieval and LLM response generation.

Phase 04 additions:
- Query classification to route retrieval
- Hybrid dense + BM25 retrieval fused with Reciprocal Rank Fusion (RRF)
- Confidence gate: abstain and escalate when top rerank score is too low
- Enhanced source citations (filename, page_number, section_title, chunk_type)
- Escalation event logging
- Document lifecycle filtering: only ACTIVE/COMPLETED docs are retrievable
"""
from typing import List, Dict, Any, Optional, Tuple, Set
from datetime import datetime
from app.services.embeddings import get_embedding_service
from app.services.vector_store import get_vector_store
from app.services.llm_service import get_llm_service
from app.services.reranker import get_reranker_service
from app.services.query_classifier import get_query_classifier, QueryClassification
from app.services.bm25_service import get_bm25_service
from app.models.enums import QueryType, DocumentStatus
from app.core.logging import get_logger
from app.config import settings

logger = get_logger(__name__)


class RAGService:
    """Service for RAG pipeline orchestration."""

    def __init__(self):
        self.embedding_service = get_embedding_service()
        self.vector_store = get_vector_store()
        self.llm_service = get_llm_service()
        self.reranker_service = get_reranker_service()
        self.classifier = get_query_classifier()
        self.bm25_service = get_bm25_service()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_active_document_ids(self, tenant_id: str) -> Set[int]:
        """
        Query the SQL database for document IDs with ACTIVE or COMPLETED status.
        Chunks from DRAFT/ARCHIVED/DEPRECATED documents are excluded from retrieval.
        """
        from app.db.session import SessionLocal
        from app.models.database import Document

        db = SessionLocal()
        try:
            rows = (
                db.query(Document.id)
                .filter(
                    Document.tenant_id == tenant_id,
                    Document.status.in_([DocumentStatus.ACTIVE, DocumentStatus.COMPLETED]),
                )
                .all()
            )
            return {r[0] for r in rows}
        finally:
            db.close()

    def _filter_by_active_docs(
        self, chunks: List[Dict[str, Any]], active_ids: Set[int]
    ) -> List[Dict[str, Any]]:
        """Remove chunks whose document_id is not in the active set."""
        return [c for c in chunks if c.get("document_id") in active_ids]

    def _refine_query_with_history(self, user_message: str, chat_history: List[Dict[str, str]]) -> str:
        """Prepend last-user-message context for follow-up questions."""
        if not chat_history:
            return user_message
        follow_up_indicators = ['it', 'that', 'this', 'they', 'also', 'and what about', 'more details']
        if any(ind in user_message.lower() for ind in follow_up_indicators):
            last_user = next(
                (m['content'] for m in reversed(chat_history) if m['role'] == 'user'), None
            )
            if last_user:
                return f"Previous context: {last_user[:100]}. Current question: {user_message}"
        return user_message

    def _rrf_merge(
        self,
        dense_chunks: List[Dict[str, Any]],
        bm25_chunks: List[Dict[str, Any]],
        k: int = None,
    ) -> List[Dict[str, Any]]:
        """
        Merge dense and BM25 ranked lists using Reciprocal Rank Fusion.
        score(d) = sum(1 / (k + rank)) across all lists.
        """
        k = k or settings.RRF_K
        scores: Dict[str, float] = {}
        meta: Dict[str, Dict[str, Any]] = {}

        def _chunk_key(chunk: Dict[str, Any]) -> str:
            return f"{chunk.get('document_id')}_{chunk.get('chunk_index')}"

        for rank, chunk in enumerate(dense_chunks, start=1):
            key = _chunk_key(chunk)
            scores[key] = scores.get(key, 0.0) + 1.0 / (k + rank)
            if key not in meta:
                meta[key] = chunk

        for rank, chunk in enumerate(bm25_chunks, start=1):
            key = _chunk_key(chunk)
            scores[key] = scores.get(key, 0.0) + 1.0 / (k + rank)
            if key not in meta:
                meta[key] = chunk

        merged = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        result = []
        for key, rrf_score in merged:
            chunk = dict(meta[key])
            chunk['score'] = rrf_score   # expose fused score for downstream use
            result.append(chunk)
        return result

    def _deduplicate_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        unique, seen = [], set()
        for chunk in chunks:
            sig = ' '.join(chunk['text'][:200].lower().split())
            if sig not in seen:
                unique.append(chunk)
                seen.add(sig)
        logger.info(f"Deduplication: {len(chunks)} → {len(unique)} chunks")
        return unique

    def _build_evidence_bundle(
        self,
        chunks: List[Dict[str, Any]],
        include_sources: bool,
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Build the LLM context string and the structured source citation list.

        Each source entry now includes: filename, page_number, section_title,
        chunk_type, relevance_score, and text snippet.
        """
        if not chunks:
            return "", []

        chunks = self._deduplicate_chunks(chunks)

        # Prefer rerank_score, fall back to RRF/vector score
        score_key = 'rerank_score' if 'rerank_score' in chunks[0] else 'score'
        chunks = sorted(chunks, key=lambda x: x.get(score_key, 0), reverse=True)

        context_parts: List[str] = []
        sources: List[Dict[str, Any]] = []

        for i, chunk in enumerate(chunks):
            score = chunk.get(score_key, 0.0)
            payload = chunk.get('metadata', chunk)  # Qdrant payload may be under 'metadata'
            page_number = payload.get('page_number') or chunk.get('page_number')
            section_title = payload.get('section_title') or chunk.get('section_title', '')
            chunk_type = payload.get('chunk_type') or chunk.get('chunk_type', 'paragraph')

            # Context block for LLM
            context_parts.append(
                f"[Source {i + 1}: {chunk['filename']}"
                + (f" | Page {page_number}" if page_number else "")
                + (f" | {section_title}" if section_title else "")
                + f" | Score: {score:.3f}]"
            )
            context_parts.append(chunk['text'])
            context_parts.append("")

            if include_sources:
                sources.append({
                    "source_number": i + 1,
                    "document_id": chunk.get('document_id'),
                    "filename": chunk.get('filename', ''),
                    "page_number": page_number,
                    "section_title": section_title,
                    "chunk_type": chunk_type,
                    "relevance_score": round(float(score), 3),
                    "snippet": chunk['text'][:500],
                })

        context = "\n".join(context_parts)
        if len(context) > settings.MAX_CONTEXT_LENGTH:
            context = context[:settings.MAX_CONTEXT_LENGTH] + "…[truncated]"
        return context, sources

    def _check_confidence(self, chunks: List[Dict[str, Any]]) -> Tuple[float, bool]:
        """
        Return (top_score, should_escalate).
        Uses rerank_score when available, otherwise RRF/vector score.
        """
        if not chunks:
            return 0.0, True
        score_key = 'rerank_score' if 'rerank_score' in chunks[0] else 'score'
        top_score = max(c.get(score_key, 0.0) for c in chunks)
        # Rerank scores are logits and can be negative; normalise to 0–1
        if score_key == 'rerank_score':
            import math
            top_score_normalised = 1.0 / (1.0 + math.exp(-top_score))
        else:
            top_score_normalised = top_score
        should_escalate = top_score_normalised < settings.ABSTENTION_THRESHOLD
        return top_score_normalised, should_escalate

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def query(
        self,
        user_message: str,
        tenant_id: str,
        company_name: str,
        session_id: str,
        chat_history: List[Dict[str, str]] = None,
        include_sources: bool = True,
        tenant_context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[str, List[Dict[str, Any]], float, bool, float, QueryType]:
        """
        Execute the full RAG pipeline.

        Returns:
            (response, sources, response_time, escalated, top_score, query_type)
        """
        start_time = datetime.utcnow()
        logger.info(f"RAG query for tenant {tenant_id}: {user_message[:100]}")

        # 1. Classify query to choose retrieval path
        classification: QueryClassification = self.classifier.classify(user_message)
        logger.info(f"Query type: {classification.query_type}, confidence: {classification.confidence:.2f}")

        # 2. Refine with history context
        refined_query = self._refine_query_with_history(user_message, chat_history or [])

        # 3. Dense retrieval
        query_embedding = await self.embedding_service.generate_embedding(refined_query)
        dense_top_k = settings.BM25_TOP_K if settings.ENABLE_BM25 else settings.TOP_K_RESULTS
        dense_chunks = await self.vector_store.search_similar(
            tenant_id=tenant_id,
            query_embedding=query_embedding,
            top_k=dense_top_k,
            score_threshold=0.05,
        )

        # 4. BM25 sparse retrieval + RRF merge
        if settings.ENABLE_BM25:
            bm25_chunks = await self.bm25_service.search(
                tenant_id=tenant_id,
                query=refined_query,
                top_k=settings.BM25_TOP_K,
            )
            all_chunks = self._rrf_merge(dense_chunks, bm25_chunks)
            logger.info(
                f"Hybrid retrieval: {len(dense_chunks)} dense + {len(bm25_chunks)} BM25 "
                f"→ {len(all_chunks)} merged"
            )
        else:
            all_chunks = dense_chunks

        # 4.5. Filter out chunks from non-active documents (DRAFT, ARCHIVED, etc.)
        active_ids = self._get_active_document_ids(tenant_id)
        all_chunks = self._filter_by_active_docs(all_chunks, active_ids)

        # 5. Rerank
        if settings.ENABLE_RERANKING and all_chunks:
            all_chunks = await self.reranker_service.rerank(
                query=user_message,
                chunks=all_chunks,
                top_k=settings.RERANK_TOP_K,
            )

        # 6. Confidence gate
        top_score, should_escalate = self._check_confidence(all_chunks)

        if should_escalate:
            logger.warning(
                f"Escalating query (top_score={top_score:.3f} < threshold={settings.ABSTENTION_THRESHOLD}) "
                f"tenant={tenant_id} session={session_id}"
            )
            escalation_msg = self._build_escalation_response(tenant_context)
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            return escalation_msg, [], elapsed, True, top_score, classification.query_type

        # 7. Build evidence bundle
        context, sources = self._build_evidence_bundle(all_chunks, include_sources)

        if not context.strip():
            escalation_msg = self._build_escalation_response(tenant_context)
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            return escalation_msg, [], elapsed, True, top_score, classification.query_type

        # 8. Generate response
        response = await self.llm_service.generate_response(
            user_message=user_message,
            context=context,
            company_name=company_name,
            chat_history=chat_history or [],
            tenant_context=tenant_context,
        )

        elapsed = (datetime.utcnow() - start_time).total_seconds()
        logger.info(f"RAG query completed in {elapsed:.2f}s (score={top_score:.3f})")
        return response, sources, elapsed, False, top_score, classification.query_type

    def _build_escalation_response(self, tenant_context: Optional[Dict[str, Any]]) -> str:
        """Return a structured escalation message with tenant contact info if available."""
        contact_parts = []
        if tenant_context:
            if tenant_context.get('support_email'):
                contact_parts.append(f"📧 {tenant_context['support_email']}")
            if tenant_context.get('support_phone'):
                contact_parts.append(f"📞 {tenant_context['support_phone']}")
            if tenant_context.get('support_url'):
                contact_parts.append(f"🔗 {tenant_context['support_url']}")
        contact_info = "\n".join(contact_parts) if contact_parts else "our support team"
        return (
            "I'm not confident I have enough information to answer that correctly.\n\n"
            "To make sure you get accurate help, please reach out to a human agent:\n"
            f"{contact_info}\n\n"
            "*This response was escalated because the available documents didn't provide "
            "sufficient evidence to answer your question.*"
        )

    async def query_stream(
        self,
        user_message: str,
        tenant_id: str,
        company_name: str,
        session_id: str,
        chat_history: List[Dict[str, str]] = None,
        tenant_context: Optional[Dict[str, Any]] = None,
    ):
        """
        Execute RAG pipeline with streaming LLM response.

        Yields:
            (chunk_text, sources, is_final, escalated, top_score, query_type)
        """
        logger.info(f"RAG streaming query for tenant {tenant_id}")

        # Classify
        classification = self.classifier.classify(user_message)
        refined_query = self._refine_query_with_history(user_message, chat_history or [])

        # Dense retrieval
        query_embedding = await self.embedding_service.generate_embedding(refined_query)
        dense_chunks = await self.vector_store.search_similar(
            tenant_id=tenant_id,
            query_embedding=query_embedding,
            top_k=settings.BM25_TOP_K if settings.ENABLE_BM25 else settings.TOP_K_RESULTS,
            score_threshold=0.05,
        )

        # BM25 + RRF
        if settings.ENABLE_BM25:
            bm25_chunks = await self.bm25_service.search(
                tenant_id=tenant_id,
                query=refined_query,
                top_k=settings.BM25_TOP_K,
            )
            all_chunks = self._rrf_merge(dense_chunks, bm25_chunks)
        else:
            all_chunks = dense_chunks

        # Filter out chunks from non-active documents
        active_ids = self._get_active_document_ids(tenant_id)
        all_chunks = self._filter_by_active_docs(all_chunks, active_ids)

        if settings.ENABLE_RERANKING and all_chunks:
            all_chunks = await self.reranker_service.rerank(
                query=user_message,
                chunks=all_chunks,
                top_k=settings.RERANK_TOP_K,
            )

        top_score, should_escalate = self._check_confidence(all_chunks)

        if should_escalate:
            escalation_msg = self._build_escalation_response(tenant_context)
            yield escalation_msg, [], True, True, top_score, classification.query_type
            return

        context, sources = self._build_evidence_bundle(all_chunks, include_sources=True)

        if not context.strip():
            escalation_msg = self._build_escalation_response(tenant_context)
            yield escalation_msg, [], True, True, top_score, classification.query_type
            return

        # Stream LLM response
        async for chunk in self.llm_service.generate_response_stream(
            user_message=user_message,
            context=context,
            company_name=company_name,
            chat_history=chat_history or [],
            tenant_context=tenant_context,
        ):
            yield chunk, sources, False, False, top_score, classification.query_type

        yield "", sources, True, False, top_score, classification.query_type


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
_rag_service: RAGService = None


def get_rag_service() -> RAGService:
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
    
def get_rag_service() -> RAGService:
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
