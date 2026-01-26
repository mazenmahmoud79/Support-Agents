/**
 * Demo user management service.
 */
import apiClient from './api';

export interface DemoUser {
    id: number;
    demo_id: string;
    tenant_id: string;
    name: string | null;
    created_at: string;
    expires_at: string | null;
    is_active: boolean;
    usage_count: number;
    last_used_at: string | null;
}

export interface CreateDemoUserRequest {
    name?: string;
    expires_in_days?: number;
}

export const demoService = {
    /**
     * Create a new demo user.
     */
    createDemoUser: async (data: CreateDemoUserRequest): Promise<DemoUser> => {
        const response = await apiClient.post<DemoUser>('/admin/demo-users', data);
        return response.data;
    },

    /**
     * List all demo users for the current tenant.
     */
    listDemoUsers: async (): Promise<DemoUser[]> => {
        const response = await apiClient.get<DemoUser[]>('/admin/demo-users');
        return response.data;
    },

    /**
     * Delete/deactivate a demo user.
     */
    deleteDemoUser: async (demoId: string): Promise<void> => {
        await apiClient.delete(`/admin/demo-users/${demoId}`);
    },
};
