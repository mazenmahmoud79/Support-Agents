/**
 * Document service for file upload and management.
 */
import apiClient from './api';
import { Document, DocumentUploadResponse, DocumentStats } from '../types';

export const documentService = {
    /**
     * Upload files.
     */
    uploadFiles: async (files: File[], category?: string): Promise<DocumentUploadResponse[]> => {
        const formData = new FormData();
        files.forEach((file) => {
            formData.append('files', file);
        });
        if (category) {
            formData.append('category', category);
        }

        const response = await apiClient.post<DocumentUploadResponse[]>(
            '/documents/upload',
            formData,
            {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
                timeout: 300000, // 5 minutes for file uploads
            }
        );
        return response.data;
    },

    /**
     * Get all documents.
     */
    listDocuments: async (params?: {
        category?: string;
        status?: string;
        skip?: number;
        limit?: number;
    }): Promise<Document[]> => {
        const response = await apiClient.get<Document[]>('/documents', { params });
        return response.data;
    },

    /**
     * Get a single document.
     */
    getDocument: async (id: number): Promise<Document> => {
        const response = await apiClient.get<Document>(`/documents/${id}`);
        return response.data;
    },

    /**
     * Update document metadata.
     */
    updateDocument: async (
        id: number,
        data: { category?: string; filename?: string }
    ): Promise<Document> => {
        const response = await apiClient.put<Document>(`/documents/${id}`, data);
        return response.data;
    },

    /**
     * Delete a document.
     */
    deleteDocument: async (id: number): Promise<void> => {
        await apiClient.delete(`/documents/${id}`);
    },

    /**
     * Batch delete documents.
     */
    batchDelete: async (documentIds: number[]): Promise<void> => {
        await apiClient.post('/documents/batch-delete', { document_ids: documentIds });
    },

    /**
     * Get document statistics.
     */
    getStats: async (): Promise<DocumentStats> => {
        const response = await apiClient.get<DocumentStats>('/documents/stats/summary');
        return response.data;
    },

    // ==================== Phase 04: Document Lifecycle (C2, C3) ====================

    /**
     * Publish a DRAFT document to ACTIVE retrieval.
     */
    publishDocument: async (documentId: number): Promise<void> => {
        await apiClient.post(`/documents/${documentId}/publish`);
    },

    /**
     * Archive an ACTIVE document (removes from retrieval, keeps data).
     */
    archiveDocument: async (documentId: number): Promise<void> => {
        await apiClient.post(`/documents/${documentId}/archive`);
    },

    /**
     * Get detailed per-document stats (chunks, language breakdown, warnings).
     */
    getDocumentStats: async (documentId: number): Promise<any> => {
        const response = await apiClient.get(`/documents/${documentId}/stats`);
        return response.data;
    },
};
