/**
 * Authentication service — register, login, Google OAuth, email verification.
 */
import apiClient from './api';
import { User } from '../types';

export interface RegisterRequest {
    email: string;
    password: string;
    org_name: string;
}

export interface LoginRequest {
    email: string;
    password: string;
}

export interface TokenResponse {
    access_token: string;
    token_type: string;
}

export const authService = {
    register: async (data: RegisterRequest): Promise<{ message: string }> => {
        const response = await apiClient.post('/auth/register', data);
        return response.data;
    },

    login: async (data: LoginRequest): Promise<TokenResponse> => {
        const response = await apiClient.post<TokenResponse>('/auth/login', data);
        return response.data;
    },

    googleAuth: async (credential: string): Promise<TokenResponse> => {
        const response = await apiClient.post<TokenResponse>('/auth/google', { credential });
        return response.data;
    },

    verifyEmail: async (token: string): Promise<TokenResponse> => {
        const response = await apiClient.get<TokenResponse>(`/auth/verify-email`, { params: { token } });
        return response.data;
    },

    resendVerification: async (email: string): Promise<{ message: string }> => {
        const response = await apiClient.post('/auth/resend-verification', { email });
        return response.data;
    },

    getCurrentUser: async (): Promise<User> => {
        const response = await apiClient.get<User>('/auth/me');
        return response.data;
    },
};
