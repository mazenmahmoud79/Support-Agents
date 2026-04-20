/**
 * Zustand state management for authentication.
 */
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { User, Tenant } from '../types';
import { authService } from '../services/authService';

interface AuthState {
    isAuthenticated: boolean;
    isVerified: boolean;
    user: User | null;
    tenant: Tenant | null;
    token: string | null;
    emailLogin: (email: string, password: string) => Promise<void>;
    googleLogin: (credential: string) => Promise<void>;
    register: (email: string, password: string, orgName: string) => Promise<{ message: string }>;
    logout: () => void;
    initialize: () => Promise<void>;
}

export const useAuthStore = create<AuthState>()(
    persist(
        (set) => ({
            isAuthenticated: false,
            isVerified: false,
            user: null,
            tenant: null,
            token: null,

            emailLogin: async (email: string, password: string) => {
                const { access_token } = await authService.login({ email, password });
                localStorage.setItem('token', access_token);
                const user = await authService.getCurrentUser();
                set({
                    isAuthenticated: true,
                    isVerified: user.is_verified,
                    user,
                    tenant: user.tenant,
                    token: access_token,
                });
            },

            googleLogin: async (credential: string) => {
                const { access_token } = await authService.googleAuth(credential);
                localStorage.setItem('token', access_token);
                const user = await authService.getCurrentUser();
                set({
                    isAuthenticated: true,
                    isVerified: user.is_verified,
                    user,
                    tenant: user.tenant,
                    token: access_token,
                });
            },

            register: async (email: string, password: string, orgName: string) => {
                return authService.register({ email, password, org_name: orgName });
            },

            logout: () => {
                localStorage.removeItem('token');
                set({ isAuthenticated: false, isVerified: false, user: null, tenant: null, token: null });
            },

            initialize: async () => {
                const token = localStorage.getItem('token');
                if (token) {
                    try {
                        const user = await authService.getCurrentUser();
                        set({
                            isAuthenticated: true,
                            isVerified: user.is_verified,
                            user,
                            tenant: user.tenant,
                            token,
                        });
                    } catch {
                        localStorage.removeItem('token');
                        set({ isAuthenticated: false, isVerified: false, user: null, tenant: null, token: null });
                    }
                }
            },
        }),
        {
            name: 'auth-storage',
            partialize: (state) => ({
                isAuthenticated: state.isAuthenticated,
                isVerified: state.isVerified,
                user: state.user,
                tenant: state.tenant,
                token: state.token,
            }),
        }
    )
);
