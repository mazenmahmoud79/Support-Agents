/**
 * Authentication service for demo login.
 */
import apiClient from './api';
import { Tenant } from '../types';

export interface DemoLoginRequest {
    demo_id: string;
}

export const authService = {
    /**
     * Login with demo ID (simplified demo access).
     */
    demoLogin: async (demoId: string): Promise<Tenant> => {
        const response = await apiClient.post<Tenant>('/auth/login', { demo_id: demoId });
        return response.data;
    },

    /**
     * Get current tenant information.
     */
    getCurrentTenant: async (): Promise<Tenant> => {
        const response = await apiClient.get<Tenant>('/auth/me');
        return response.data;
    },
};
