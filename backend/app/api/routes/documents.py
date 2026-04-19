"""
Document management routes for uploading, listing, updating, and deleting documents.

Phase 04 additions:
- C2: Explicit publish (→ ACTIVE) and archive (→ ARCHIVED) actions
- C3: Per-document detailed stats endpoint
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.session import get_db
from app.api.deps import get_current_tenant
from app.models.database import Tenant, Document
from app.models.schemas import (
    DocumentUploadResponse,
    DocumentResponse,
    DocumentUpdate,
    BulkDeleteRequest,
    DocumentStats,
    DocumentLifecycleResponse,
    DocumentDetailStats,
)
from app.models.enums import FileType, DocumentStatus
from app.services.document_processor import get_document_processor
from app.services.embeddings import get_embedding_service
from app.services.vector_store import get_vector_store
from app.services.bm25_service import get_bm25_service
from app.config import settings
from app.core.logging import get_logger
from datetime import datetime
import asyncio

logger = get_logger(__name__)

router = APIRouter(prefix="/documents", tags=["Documents"])

# Statuses that are included in retrieval
_ACTIVE_STATUSES = {DocumentStatus.ACTIVE, DocumentStatus.COMPLETED}


@router.post("/upload", response_model=List[DocumentUploadResponse])
async def upload_documents(
    files: List[UploadFile] = File(..., description="Files to upload (PDF, DOCX, TXT, CSV)"),
    category: Optional[str] = Form(None, description="Document category"),
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """
    Upload one or more documents for processing.
    
    Files are parsed, chunked, embedded, and stored in the vector database.
    """
    logger.info(f"Uploading {len(files)} files for tenant {tenant.tenant_id}")
    
    document_processor = get_document_processor()
    embedding_service = get_embedding_service()
    vector_store = get_vector_store()
    
    results = []
    
    for file in files:
        try:
            # Validate file type
            file_ext = file.filename.split('.')[-1].lower()
            if f".{file_ext}" not in settings.ALLOWED_EXTENSIONS:
                results.append(DocumentUploadResponse(
                    document_id=0,
                    filename=file.filename,
                    file_type=FileType.TXT,  # Default
                    file_size=0,
                    status=DocumentStatus.FAILED,
                    message=f"Unsupported file type: {file_ext}"
                ))
                continue
            
            # Determine file type
            file_type = FileType(file_ext)
            
            # Read file content
            content = await file.read()
            file_size = len(content)
            
            # Validate file size
            if file_size > settings.MAX_UPLOAD_SIZE:
                results.append(DocumentUploadResponse(
                    document_id=0,
                    filename=file.filename,
                    file_type=file_type,
                    file_size=file_size,
                    status=DocumentStatus.FAILED,
                    message=f"File too large (max {settings.MAX_UPLOAD_SIZE} bytes)"
                ))
                continue
            
            # Create document record
            document = Document(
                tenant_id=tenant.tenant_id,
                filename=file.filename,
                file_type=file_type,
                file_size=file_size,
                category=category,
                status=DocumentStatus.PROCESSING,
                collection_name=vector_store._get_collection_name(tenant.tenant_id)
            )
            
            db.add(document)
            db.commit()
            db.refresh(document)
            
            # Process file (async)
            try:
                chunks, metadata = await document_processor.process_file(
                    file_content=content,
                    filename=file.filename,
                    file_type=file_type
                )
                
                # Generate embeddings for all chunks
                texts = [chunk.text for chunk in chunks]
                embeddings = await embedding_service.generate_embeddings_batch(texts)
                
                # Prepare chunks for vector store
                chunk_data = []
                for chunk in chunks:
                    chunk_data.append({
                        "text": chunk.text,
                        "metadata": chunk.metadata
                    })
                
                # Store in vector database
                vectors_count = await vector_store.upsert_vectors(
                    tenant_id=tenant.tenant_id,
                    document_id=document.id,
                    chunks=chunk_data,
                    embeddings=embeddings
                )
                
                # Update document status — DRAFT awaits admin publish action
                document.chunk_count = len(chunks)
                document.status = DocumentStatus.DRAFT
                db.commit()

                # Invalidate BM25 cache so next query rebuilds with new chunks
                get_bm25_service().invalidate(tenant.tenant_id)
                
                logger.info(f"Successfully processed {file.filename}: {len(chunks)} chunks → DRAFT")
                
                results.append(DocumentUploadResponse(
                    document_id=document.id,
                    filename=file.filename,
                    file_type=file_type,
                    file_size=file_size,
                    status=DocumentStatus.DRAFT,
                    message=f"Processed successfully: {len(chunks)} chunks. Awaiting admin publish."
                ))
                
            except Exception as e:
                logger.error(f"Error processing {file.filename}: {e}")
                document.status = DocumentStatus.FAILED
                document.error_message = str(e)
                db.commit()
                
                results.append(DocumentUploadResponse(
                    document_id=document.id,
                    filename=file.filename,
                    file_type=file_type,
                    file_size=file_size,
                    status=DocumentStatus.FAILED,
                    message=f"Processing failed: {str(e)}"
                ))
        
        except Exception as e:
            logger.error(f"Error uploading {file.filename}: {e}")
            results.append(DocumentUploadResponse(
                document_id=0,
                filename=file.filename,
                file_type=FileType.TXT,
                file_size=0,
                status=DocumentStatus.FAILED,
                message=f"Upload failed: {str(e)}"
            ))
    
    return results


@router.get("", response_model=List[DocumentResponse])
async def list_documents(
    category: Optional[str] = Query(None, description="Filter by category"),
    status: Optional[DocumentStatus] = Query(None, description="Filter by status"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """
    List all documents for the authenticated tenant.
    """
    query = db.query(Document).filter(Document.tenant_id == tenant.tenant_id)
    
    if category:
        query = query.filter(Document.category == category)
    if status:
        query = query.filter(Document.status == status)
    
    documents = query.order_by(Document.upload_date.desc()).offset(skip).limit(limit).all()
    
    return documents


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """
    Get details of a specific document.
    """
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.tenant_id == tenant.tenant_id
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    return document


@router.put("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: int,
    update_data: DocumentUpdate,
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """
    Update document metadata.
    """
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.tenant_id == tenant.tenant_id
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Update fields
    if update_data.category is not None:
        document.category = update_data.category
    if update_data.filename is not None:
        document.filename = update_data.filename
    
    db.commit()
    db.refresh(document)
    
    logger.info(f"Updated document {document_id}")
    
    return document


@router.delete("/{document_id}")
async def delete_document(
    document_id: int,
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """
    Delete a document and its vectors from the vector database.
    """
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.tenant_id == tenant.tenant_id
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Delete vectors from Qdrant
    vector_store = get_vector_store()
    try:
        await vector_store.delete_document_vectors(tenant.tenant_id, document_id)
        logger.info(f"Deleted vectors for document {document_id}")
    except Exception as e:
        logger.error(f"Error deleting vectors: {e}")
        # Continue with database deletion even if vector deletion fails
    
    # Delete from database
    db.delete(document)
    db.commit()

    # Invalidate BM25 cache so deleted doc is excluded
    get_bm25_service().invalidate(tenant.tenant_id)
    
    logger.info(f"Deleted document {document_id}")
    
    return {"message": "Document deleted successfully"}


@router.post("/batch-delete")
async def batch_delete_documents(
    delete_request: BulkDeleteRequest,
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """
    Delete multiple documents in batch.
    """
    logger.info(f"Batch deleting {len(delete_request.document_ids)} documents")
    
    vector_store = get_vector_store()
    deleted_count = 0
    errors = []
    
    for document_id in delete_request.document_ids:
        try:
            document = db.query(Document).filter(
                Document.id == document_id,
                Document.tenant_id == tenant.tenant_id
            ).first()
            
            if not document:
                errors.append({"document_id": document_id, "error": "Not found"})
                continue
            
            # Delete vectors
            await vector_store.delete_document_vectors(tenant.tenant_id, document_id)
            
            # Delete from database
            db.delete(document)
            deleted_count += 1
            
        except Exception as e:
            logger.error(f"Error deleting document {document_id}: {e}")
            errors.append({"document_id": document_id, "error": str(e)})
    
    db.commit()

    # Invalidate BM25 cache after batch deletion
    if deleted_count > 0:
        get_bm25_service().invalidate(tenant.tenant_id)
    
    return {
        "deleted_count": deleted_count,
        "total_requested": len(delete_request.document_ids),
        "errors": errors
    }


@router.get("/stats/summary", response_model=DocumentStats)
async def get_document_stats(
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """
    Get document statistics for the tenant.
    """
    # Total documents
    total = db.query(func.count(Document.id)).filter(
        Document.tenant_id == tenant.tenant_id
    ).scalar()
    
    # Total chunks
    total_chunks = db.query(func.sum(Document.chunk_count)).filter(
        Document.tenant_id == tenant.tenant_id
    ).scalar() or 0
    
    # Total size
    total_size = db.query(func.sum(Document.file_size)).filter(
        Document.tenant_id == tenant.tenant_id
    ).scalar() or 0
    
    # Documents by type
    type_counts = db.query(
        Document.file_type, func.count(Document.id)
    ).filter(
        Document.tenant_id == tenant.tenant_id
    ).group_by(Document.file_type).all()
    
    documents_by_type = {str(file_type): count for file_type, count in type_counts}
    
    # Recent uploads (last 10)
    recent = db.query(Document).filter(
        Document.tenant_id == tenant.tenant_id
    ).order_by(Document.upload_date.desc()).limit(10).all()
    
    return DocumentStats(
        total_documents=total,
        total_chunks=int(total_chunks),
        total_size_bytes=int(total_size),
        documents_by_type=documents_by_type,
        recent_uploads=recent
    )


# ==================== Phase 04: Document Lifecycle (C2 + C3) ====================

@router.post("/{document_id}/publish", response_model=DocumentLifecycleResponse)
async def publish_document(
    document_id: int,
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db),
):
    """
    Explicitly publish a DRAFT document to ACTIVE retrieval.

    Publishing is a deliberate admin action — documents never become ACTIVE automatically.
    """
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.tenant_id == tenant.tenant_id,
    ).first()

    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    if document.status not in {DocumentStatus.DRAFT, DocumentStatus.ARCHIVED}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only DRAFT or ARCHIVED documents can be published. Current status: {document.status}",
        )

    document.status = DocumentStatus.ACTIVE
    db.commit()
    # No BM25 invalidation needed here — ACTIVE docs are already indexed

    logger.info(f"Document {document_id} published to ACTIVE by tenant {tenant.tenant_id}")
    return DocumentLifecycleResponse(
        document_id=document.id,
        filename=document.filename,
        status=DocumentStatus.ACTIVE,
        message="Document is now ACTIVE and included in retrieval.",
    )


@router.post("/{document_id}/archive", response_model=DocumentLifecycleResponse)
async def archive_document(
    document_id: int,
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db),
):
    """
    Archive an ACTIVE document — removes it from retrieval without deleting it.
    """
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.tenant_id == tenant.tenant_id,
    ).first()

    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    document.status = DocumentStatus.ARCHIVED
    db.commit()

    # Invalidate BM25 cache so archived doc is excluded from next search
    get_bm25_service().invalidate(tenant.tenant_id)

    logger.info(f"Document {document_id} archived by tenant {tenant.tenant_id}")
    return DocumentLifecycleResponse(
        document_id=document.id,
        filename=document.filename,
        status=DocumentStatus.ARCHIVED,
        message="Document archived and removed from retrieval.",
    )


@router.get("/{document_id}/stats", response_model=DocumentDetailStats)
async def get_document_detail_stats(
    document_id: int,
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db),
):
    """
    Return per-document stats for admin review before publishing.

    Includes chunk count, language distribution, chunk type breakdown,
    page count, and any parsing warnings.
    """
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.tenant_id == tenant.tenant_id,
    ).first()

    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    # Fetch chunk metadata from vector store to compute distributions
    vector_store = get_vector_store()
    client = await vector_store._get_client()
    collection_name = vector_store._get_collection_name(tenant.tenant_id)

    language_dist: dict = {}
    chunk_type_dist: dict = {}
    page_count: int = 0
    warnings: list = []

    try:
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        offset = None
        while True:
            scroll_kwargs = dict(
                collection_name=collection_name,
                limit=200,
                with_payload=True,
                with_vectors=False,
                scroll_filter=Filter(
                    must=[FieldCondition(key="document_id", match=MatchValue(value=document_id))]
                ),
            )
            if offset is not None:
                scroll_kwargs["offset"] = offset

            result = client.scroll(**scroll_kwargs)
            points, next_offset = result if isinstance(result, tuple) else (result, None)

            for point in points:
                payload = point.payload or {}
                lang = payload.get("language", "unknown")
                language_dist[lang] = language_dist.get(lang, 0) + 1

                ctype = payload.get("chunk_type", "paragraph")
                chunk_type_dist[ctype] = chunk_type_dist.get(ctype, 0) + 1

                pg = payload.get("page_number")
                if pg and pg > page_count:
                    page_count = pg

                if payload.get("ocr_confidence") and payload["ocr_confidence"] < 0.6:
                    warnings.append(
                        f"Low OCR confidence ({payload['ocr_confidence']:.2f}) on page {pg or '?'}"
                    )

            if not next_offset:
                break
            offset = next_offset
    except Exception as exc:
        logger.warning(f"Could not fetch chunk details for document {document_id}: {exc}")
        warnings.append("Could not fetch detailed chunk metadata from vector store.")

    return DocumentDetailStats(
        document_id=document.id,
        filename=document.filename,
        status=document.status,
        chunk_count=document.chunk_count or 0,
        file_type=document.file_type.value,
        file_size=document.file_size,
        upload_date=document.upload_date,
        language_distribution=language_dist,
        chunk_type_breakdown=chunk_type_dist,
        parsing_warnings=warnings,
        page_count=page_count if page_count > 0 else None,
    )
