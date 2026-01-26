/**
 * Zustand state management for authentication.
 */
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { Tenant } from '../types';
import { authService } from '../services/authService';

interface AuthState {
    isAuthenticated: boolean;
    tenant: Tenant | null;
    apiKey: string | null;
    demoLogin: (demoId: string) => Promise<void>;
    logout: () => void;
    initialize: () => Promise<void>;
    setApiKey: (key: string) => void;
}

export const useAuthStore = create<AuthState>()(
    persist(
        (set) => ({
            isAuthenticated: false,
            tenant: null,
            apiKey: null,

            demoLogin: async (demoId: string) => {
                const tenant = await authService.demoLogin(demoId);
                localStorage.setItem('apiKey', tenant.api_key);
                localStorage.setItem('demoId', demoId);
                set({ isAuthenticated: true, tenant, apiKey: tenant.api_key });
            },

            logout: () => {
                localStorage.removeItem('apiKey');
                localStorage.removeItem('demoId');
                set({ isAuthenticated: false, tenant: null, apiKey: null });
            },

            initialize: async () => {
                const apiKey = localStorage.getItem('apiKey');
                if (apiKey) {
                    try {
                        const tenant = await authService.getCurrentTenant();
                        set({ isAuthenticated: true, tenant, apiKey });
                    } catch (error) {
                        localStorage.removeItem('apiKey');
                        set({ isAuthenticated: false, tenant: null, apiKey: null });
                    }
                }
            },

            setApiKey: (key: string) => {
                localStorage.setItem('apiKey', key);
                set((state) => ({
                    apiKey: key,
                    tenant: state.tenant ? { ...state.tenant, api_key: key } : null
                }));
            }
        }),
        {
            name: 'auth-storage',
            partialize: (state) => ({
                isAuthenticated: state.isAuthenticated,
                tenant: state.tenant,
                apiKey: state.apiKey,
            }),
        }
    )
);
