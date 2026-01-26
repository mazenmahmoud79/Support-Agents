/**
 * Tenant Context Service for managing company settings and AI customization.
 */
import apiClient from './api';
import { TenantContext, TenantContextUpdate, ContextOptions } from '../types';

export interface TokenInfo {
    tenant_id: string;
    token_preview: string;
    message: string;
}

export interface RegenerateTokenResponse {
    message: string;
    api_key: string;
    warning: string;
    tenant_id: string;
}

export const tenantContextService = {
    /**
     * Get the current tenant's context/profile settings.
     * Returns existing settings or creates default settings if none exist.
     */
    async getContext(): Promise<TenantContext> {
        const response = await apiClient.get<TenantContext>('/admin/context');
        return response.data;
    },

    /**
     * Update the current tenant's context/profile settings.
     * Only provided fields are updated (partial update supported).
     */
    async updateContext(data: TenantContextUpdate): Promise<TenantContext> {
        const response = await apiClient.put<TenantContext>('/admin/context', data);
        return response.data;
    },

    /**
     * Get all available options for tenant context dropdowns.
     * Used to populate form select fields.
     */
    async getContextOptions(): Promise<ContextOptions> {
        const response = await apiClient.get<ContextOptions>('/admin/context/options');
        return response.data;
    },

    /**
     * Get information about the current API token (masked preview).
     */
    async getTokenInfo(): Promise<TokenInfo> {
        const response = await apiClient.get<TokenInfo>('/admin/token-info');
        return response.data;
    },

    /**
     * Regenerate API token. The new token is only shown once!
     * Old token is invalidated immediately.
     */
    async regenerateToken(): Promise<RegenerateTokenResponse> {
        const response = await apiClient.post<RegenerateTokenResponse>('/admin/regenerate-token');
        return response.data;
    },
};

export default tenantContextService;

