/**
 * Axios HTTP client configuration and API service.
 */
import axios, { AxiosInstance } from 'axios';

const API_BASE_URL = (import.meta as any).env?.VITE_API_URL || 'http://localhost:8000/api';

// Create axios instance
const apiClient: AxiosInstance = axios.create({
    baseURL: API_BASE_URL,
    timeout: 30000,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Request interceptor to add API key
apiClient.interceptors.request.use(
    (config) => {
        const apiKey = localStorage.getItem('apiKey');
        if (apiKey) {
            config.headers['X-API-Key'] = apiKey;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            // Unauthorized - clear auth and redirect
            localStorage.removeItem('apiKey');
            localStorage.removeItem('tenant');
            window.location.href = '/login';
        }
        return Promise.reject(error);
    }
);

export default apiClient;
