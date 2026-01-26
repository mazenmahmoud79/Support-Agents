"""
Vector store service using Qdrant for semantic search.
"""
import asyncio
import uuid
from typing import List, Dict, Any, Optional, Tuple
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    SearchRequest,
)
from app.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class VectorStoreService:
    """Service for managing Qdrant vector database operations."""
    
    def __init__(self):
        """Initialize Qdrant client."""
        self.client = None
        self._client_lock = asyncio.Lock()
    
    async def _get_client(self) -> QdrantClient:
        """Get or create Qdrant client (lazy initialization)."""
        if self.client is None:
            async with self._client_lock:
                if self.client is None:  # Double-check
                    logger.info(f"Connecting to Qdrant at {settings.QDRANT_HOST}:{settings.QDRANT_PORT}")
                    self.client = QdrantClient(
                        host=settings.QDRANT_HOST,
                        port=settings.QDRANT_PORT,
                        api_key=settings.QDRANT_API_KEY,
                        timeout=30,
                        prefer_grpc=False,  # Use HTTP instead of gRPC
                        https=False  # Disable HTTPS for local development
                    )
                    logger.info("Qdrant client initialized")
        return self.client
    
    def _get_collection_name(self, tenant_id: str) -> str:
        """
        Get collection name for a tenant.
        
        Args:
            tenant_id: Tenant ID
        
        Returns:
            str: Collection name
        """
        return f"{settings.QDRANT_COLLECTION_PREFIX}{tenant_id}"
    
    async def create_collection(self, tenant_id: str) -> bool:
        """
        Create a collection for a tenant.
        
        Args:
            tenant_id: Tenant ID
        
        Returns:
            bool: True if created, False if already exists
        """
        client = await self._get_client()
        collection_name = self._get_collection_name(tenant_id)
        
        try:
            # Check if collection exists
            collections = client.get_collections().collections
            collection_names = [col.name for col in collections]
            
            if collection_name in collection_names:
                logger.info(f"Collection {collection_name} already exists")
                return False
            
            # Create collection with vector configuration
            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=settings.EMBEDDING_DIMENSION,
                    distance=Distance.COSINE
                )
            )
            
            logger.info(f"Created collection: {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating collection {collection_name}: {e}")
            raise
    
    async def upsert_vectors(
        self,
        tenant_id: str,
        document_id: int,
        chunks: List[Dict[str, Any]],
        embeddings: List[List[float]]
    ) -> int:
        """
        Upsert vectors for document chunks.
        
        Args:
            tenant_id: Tenant ID
            document_id: Document ID
            chunks: List of chunk metadata
            embeddings: List of embedding vectors
        
        Returns:
            int: Number of vectors inserted
        """
        client = await self._get_client()
        collection_name = self._get_collection_name(tenant_id)
        
        # Ensure collection exists
        await self.create_collection(tenant_id)
        
        # Create points for upsert
        points = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            # Qdrant requires point_id to be int or UUID. We use deterministic UUID based on doc_id and index.
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{document_id}_{i}"))
            
            # Prepare payload with metadata
            payload = {
                "document_id": document_id,
                "tenant_id": tenant_id,
                "chunk_index": i,
                "text": chunk["text"],
                "filename": chunk["metadata"]["filename"],
                **chunk["metadata"]
            }
            
            point = PointStruct(
                id=point_id,
                vector=embedding,
                payload=payload
            )
            points.append(point)
        
        # Upsert in batches
        batch_size = 100
        for i in range(0, len(points), batch_size):
            batch = points[i:i + batch_size]
            client.upsert(
                collection_name=collection_name,
                points=batch,
                wait=True
            )
        
        logger.info(f"Upserted {len(points)} vectors for document {document_id}")
        return len(points)
    
    async def search_similar(
        self,
        tenant_id: str,
        query_embedding: List[float],
        top_k: int = None,
        score_threshold: float = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors.
        
        Args:
            tenant_id: Tenant ID
            query_embedding: Query vector
            top_k: Number of results to return
            score_threshold: Minimum similarity score
        
        Returns:
            List of results with scores and metadata
        """
        client = await self._get_client()
        collection_name = self._get_collection_name(tenant_id)
        
        if top_k is None:
            top_k = settings.TOP_K_RESULTS
        if score_threshold is None:
            # Hardcode to 0.1 for now to bypass settings caching issue
            score_threshold = 0.1  # settings.SIMILARITY_THRESHOLD
        
        try:
            # Debug: Check client attributes
            # logger.info(f"QdrantClient attributes: {dir(client)}")
            
            # Debug: Log query stats
            logger.info(f"Query embedding stats - Length: {len(query_embedding)}, First 5: {query_embedding[:5]}")
            
            # Robust search implementation supporting multiple client versions
            if hasattr(client, 'search'):
                # Qdrant client 1.7+
                logger.info("Using client.search method")
                results = client.search(
                    collection_name=collection_name,
                    query_vector=query_embedding,
                    limit=top_k,
                    score_threshold=score_threshold
                )
            
            elif hasattr(client, 'search_batch'):
                # Qdrant client intermediate versions or specific configs
                logger.info("Using client.search_batch method")
                search_queries = [
                    SearchRequest(
                        vector=query_embedding,
                        limit=top_k,
                        with_payload=True
                    )
                ]
                batch_results = client.search_batch(
                    collection_name=collection_name,
                    requests=search_queries
                )
                results = batch_results[0] if batch_results else []
                logger.info(f"Raw batch results count: {len(results)}")
                if results:
                    logger.info(f"Top result score: {results[0].score}")
                
                if score_threshold:
                     results = [r for r in results if r.score >= score_threshold]
                     
            elif hasattr(client, 'query_points'):
                # Qdrant client alternate API (e.g. QdrantRemote)
                # Note: query_points usually expects 'query' arg, not 'query_vector'
                logger.info("Using client.query_points method")
                response = client.query_points(
                    collection_name=collection_name,
                    query=query_embedding,
                    limit=top_k,
                    with_payload=True
                )
                logger.info(f"query_points response type: {type(response)}")
                logger.info(f"query_points raw points count: {len(response.points) if response.points else 0}")
                if response.points:
                    logger.info(f"First result score: {response.points[0].score}")
                    
                results = response.points
                if score_threshold and results:
                    before_filter = len(results)
                    results = [r for r in results if r.score >= score_threshold]
                    logger.info(f"After threshold filter ({score_threshold}): {before_filter} -> {len(results)}")
            
            elif hasattr(client, 'search_points'):
                 # Legacy Qdrant
                 logger.info("Using client.search_points method")
                 results = client.search_points(
                    collection_name=collection_name,
                    vector=query_embedding,
                    limit=top_k,
                    with_payload=True
                 )
                 if score_threshold:
                     results = [r for r in results if r.score >= score_threshold]
            
            else:
                logger.error(f"No compatible search method found on QdrantClient. Available: {[m for m in dir(client) if 'search' in m or 'query' in m]}")
                return []
            
            # Format results
            formatted_results = []
            for result in results:
                payload = result.payload or {}
                formatted_results.append({
                    "id": result.id,
                    "score": result.score,
                    "document_id": payload.get("document_id"),
                    "chunk_index": payload.get("chunk_index"),
                    "filename": payload.get("filename"),
                    "text": payload.get("text"),
                    "metadata": payload
                })
            
            logger.info(f"Found {len(formatted_results)} similar chunks for tenant {tenant_id}")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching in collection {collection_name}: {e}")
            # Return empty if collection doesn't exist yet
            return []
    
    async def delete_document_vectors(
        self,
        tenant_id: str,
        document_id: int
    ) -> int:
        """
        Delete all vectors for a document.
        
        Args:
            tenant_id: Tenant ID
            document_id: Document ID
        
        Returns:
            int: Number of vectors deleted
        """
        client = await self._get_client()
        collection_name = self._get_collection_name(tenant_id)
        
        try:
            # Delete by filter
            client.delete(
                collection_name=collection_name,
                points_selector=Filter(
                    must=[
                        FieldCondition(
                            key="document_id",
                            match=MatchValue(value=document_id)
                        )
                    ]
                )
            )
            
            logger.info(f"Deleted vectors for document {document_id}")
            return 1  # Qdrant doesn't return count
            
        except Exception as e:
            logger.error(f"Error deleting vectors for document {document_id}: {e}")
            raise
    
    async def delete_collection(self, tenant_id: str) -> bool:
        """
        Delete a tenant's collection.
        
        Args:
            tenant_id: Tenant ID
        
        Returns:
            bool: True if deleted
        """
        client = await self._get_client()
        collection_name = self._get_collection_name(tenant_id)
        
        try:
            client.delete_collection(collection_name=collection_name)
            logger.info(f"Deleted collection: {collection_name}")
            return True
        except Exception as e:
            logger.error(f"Error deleting collection {collection_name}: {e}")
            return False
    
    async def get_collection_stats(self, tenant_id: str) -> Dict[str, Any]:
        """
        Get statistics for a tenant's collection.
        
        Args:
            tenant_id: Tenant ID
        
        Returns:
            Dict with collection statistics
        """
        client = await self._get_client()
        collection_name = self._get_collection_name(tenant_id)
        
        try:
            info = client.get_collection(collection_name=collection_name)
            return {
                "name": collection_name,
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
                "status": info.status
            }
        except Exception as e:
            logger.warning(f"Collection {collection_name} not found: {e}")
            return {
                "name": collection_name,
                "vectors_count": 0,
                "points_count": 0,
                "status": "not_found"
            }
    
    async def health_check(self) -> bool:
        """
        Check if Qdrant is healthy.
        
        Returns:
            bool: True if healthy
        """
        try:
            client = await self._get_client()
            collections = client.get_collections()
            return True
        except Exception as e:
            logger.error(f"Qdrant health check failed: {e}")
            return False


# Global vector store service instance
_vector_store_service: VectorStoreService = None


def get_vector_store() -> VectorStoreService:
    """
    Get the global vector store service instance.
    
    Returns:
        VectorStoreService: Vector store service
    """
    global _vector_store_service
    if _vector_store_service is None:
        _vector_store_service = VectorStoreService()
    return _vector_store_service
