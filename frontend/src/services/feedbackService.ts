/**
 * Feedback service — Phase 04 B2/B4.
 * Handles thumbs up/down and agent corrections.
 */
import apiClient from './api';
import {
    FeedbackRequest,
    AgentCorrectionRequest,
    ImprovementQueueItem,
    ImprovementStatus,
} from '../types';

export const feedbackService = {
    /**
     * Submit thumbs-up or thumbs-down feedback on an assistant message.
     */
    submitFeedback: async (req: FeedbackRequest): Promise<void> => {
        await apiClient.post('/chat/feedback', req);
    },

    /**
     * Submit an agent correction for an assistant response.
     */
    submitCorrection: async (req: AgentCorrectionRequest): Promise<void> => {
        await apiClient.post('/chat/feedback/correction', req);
    },

    /**
     * List all feedback entries (admin).
     */
    listFeedback: async (params?: {
        feedback_type?: string;
        improvement_status?: ImprovementStatus;
        limit?: number;
        skip?: number;
    }): Promise<any[]> => {
        const response = await apiClient.get('/admin/feedback', { params });
        return response.data;
    },

    /**
     * Get items in the improvement queue (admin).
     */
    listImprovementQueue: async (params?: {
        limit?: number;
        skip?: number;
    }): Promise<ImprovementQueueItem[]> => {
        const response = await apiClient.get('/admin/feedback/improvement-queue', { params });
        return response.data;
    },

    /**
     * Update the status of a feedback/improvement item (admin).
     * Backend expects `new_status` as a query parameter.
     */
    updateImprovementStatus: async (
        id: number,
        newStatus: ImprovementStatus
    ): Promise<void> => {
        await apiClient.patch(`/admin/feedback/${id}/status`, null, {
            params: { new_status: newStatus },
        });
    },
};
