"""
BM25 sparse-retrieval service.

Maintains a per-tenant in-memory BM25 index built from Qdrant payloads.
The index is rebuilt lazily on the first query after a document is added or
removed (cache invalidation via `invalidate`).
"""
import asyncio
from typing import Dict, List, Any, Optional
from rank_bm25 import BM25Okapi
from app.core.logging import get_logger

logger = get_logger(__name__)

# Simple tokeniser — split on whitespace; Arabic and English friendly
def _tokenize(text: str) -> List[str]:
    return text.lower().split()


class TenantBM25Index:
    """Holds a BM25 index and its source chunk list for one tenant."""

    def __init__(self, chunks: List[Dict[str, Any]]):
        self.chunks = chunks
        tokenised = [_tokenize(c["text"]) for c in chunks]
        self.bm25 = BM25Okapi(tokenised) if tokenised else None

    def search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        if not self.bm25 or not self.chunks:
            return []
        tokens = _tokenize(query)
        scores = self.bm25.get_scores(tokens)
        # Pair each score with its chunk and sort descending
        scored = sorted(
            zip(scores, self.chunks), key=lambda x: x[0], reverse=True
        )
        results = []
        for raw_score, chunk in scored[:top_k]:
            enriched = dict(chunk)
            enriched["bm25_score"] = float(raw_score)
            results.append(enriched)
        return results


class BM25Service:
    """
    Per-tenant BM25 index manager.

    Usage:
        service = BM25Service(vector_store)
        results = await service.search(tenant_id, query, top_k=10)
        service.invalidate(tenant_id)   # call after upload or delete
    """

    def __init__(self, vector_store):
        self._vector_store = vector_store
        self._indexes: Dict[str, TenantBM25Index] = {}
        self._lock = asyncio.Lock()

    def invalidate(self, tenant_id: str) -> None:
        """Evict the cached index for a tenant (triggers a rebuild on next search)."""
        self._indexes.pop(tenant_id, None)
        logger.info(f"BM25 index invalidated for tenant {tenant_id}")

    async def _build_index(self, tenant_id: str) -> TenantBM25Index:
        """Scroll all Qdrant payloads and build a fresh BM25 index."""
        client = await self._vector_store._get_client()
        collection_name = self._vector_store._get_collection_name(tenant_id)

        chunks: List[Dict[str, Any]] = []
        try:
            offset = None
            while True:
                scroll_kwargs: Dict[str, Any] = dict(
                    collection_name=collection_name,
                    limit=200,
                    with_payload=True,
                    with_vectors=False,
                )
                if offset is not None:
                    scroll_kwargs["offset"] = offset

                result = client.scroll(**scroll_kwargs)
                # result is a tuple: (List[ScoredPoint], Optional[next_offset])
                points, next_offset = result if isinstance(result, tuple) else (result, None)

                for point in points:
                    payload = point.payload or {}
                    text = payload.get("text", "")
                    if text.strip():
                        chunks.append({
                            "id": str(point.id),
                            "text": text,
                            "document_id": payload.get("document_id"),
                            "chunk_index": payload.get("chunk_index"),
                            "filename": payload.get("filename", ""),
                            "score": 0.0,   # placeholder; will be set by BM25
                            "metadata": payload,
                        })

                if not next_offset:
                    break
                offset = next_offset

        except Exception as exc:
            logger.warning(f"BM25 index build failed for {tenant_id}: {exc}")

        logger.info(
            f"Built BM25 index for tenant {tenant_id}: {len(chunks)} chunks"
        )
        return TenantBM25Index(chunks)

    async def search(
        self, tenant_id: str, query: str, top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Return BM25 ranked chunks for *query*.

        Builds (and caches) the tenant index on the first call.
        """
        if tenant_id not in self._indexes:
            async with self._lock:
                if tenant_id not in self._indexes:
                    self._indexes[tenant_id] = await self._build_index(tenant_id)

        return self._indexes[tenant_id].search(query, top_k)


# ---------------------------------------------------------------------------
# Module-level singleton (initialised after vector_store is available)
# ---------------------------------------------------------------------------
_bm25_service: Optional[BM25Service] = None


def get_bm25_service() -> BM25Service:
    global _bm25_service
    if _bm25_service is None:
        from app.services.vector_store import get_vector_store
        _bm25_service = BM25Service(get_vector_store())
    return _bm25_service
