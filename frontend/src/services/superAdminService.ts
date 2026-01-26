import apiClient from './api';

export interface TenantInfo {
    id: number;
    tenant_id: string;
    name: string;
    demo_id: string;
    slug: string | null;
    is_active: boolean;
    created_at: string;
    document_count: number;
}

export interface TenantListResponse {
    tenants: TenantInfo[];
    total: number;
}

export interface AdminStats {
    total_tenants: number;
    active_tenants: number;
    inactive_tenants: number;
    total_documents: number;
}

class SuperAdminService {
    private password: string | null = null;

    setPassword(password: string) {
        this.password = password;
        sessionStorage.setItem('superAdminAuth', password);
    }

    getPassword(): string | null {
        if (!this.password) {
            this.password = sessionStorage.getItem('superAdminAuth');
        }
        return this.password;
    }

    clearAuth() {
        this.password = null;
        sessionStorage.removeItem('superAdminAuth');
    }

    isAuthenticated(): boolean {
        return !!this.getPassword();
    }

    async login(password: string): Promise<boolean> {
        const response = await apiClient.post('/super-admin/login', { password });
        if (response.data.success) {
            this.setPassword(password);
            return true;
        }
        return false;
    }

    async getStats(): Promise<AdminStats> {
        const response = await apiClient.get('/super-admin/stats');
        return response.data;
    }

    async listTenants(): Promise<TenantListResponse> {
        const response = await apiClient.get('/super-admin/tenants');
        return response.data;
    }

    async createTenant(name: string): Promise<TenantInfo> {
        const response = await apiClient.post('/super-admin/tenants', { name });
        return response.data;
    }

    async updateTenant(tenantId: string, data: { is_active?: boolean; name?: string }): Promise<void> {
        await apiClient.patch(`/super-admin/tenants/${tenantId}`, data);
    }

    async deleteTenant(tenantId: string): Promise<void> {
        await apiClient.delete(`/super-admin/tenants/${tenantId}`);
    }
}

export const superAdminService = new SuperAdminService();
