/**
 * Chat service for conversations with streaming support.
 */
import apiClient from './api';
import { ChatResponse, ChatMessage } from '../types';

export interface ChatRequest {
    message: string;
    session_id: string;
    include_sources?: boolean;
}

export const chatService = {
    /**
     * Send a chat message and get response.
     */
    sendMessage: async (request: ChatRequest): Promise<ChatResponse> => {
        const response = await apiClient.post<ChatResponse>('/chat', {
            message: request.message,
            session_id: request.session_id,
            include_sources: request.include_sources ?? true,
        });
        return response.data;
    },

    /**
     * Send a message with streaming response.
     */
    sendMessageStream: async (
        request: ChatRequest,
        onChunk: (chunk: string) => void,
        onComplete: (sources: any[], responseTime: number) => void,
        onError: (error: Error) => void
    ): Promise<void> => {
        const apiKey = localStorage.getItem('apiKey');
        const apiUrl = apiClient.defaults.baseURL;

        try {
            const response = await fetch(`${apiUrl}/chat/stream`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-API-Key': apiKey || '',
                },
                body: JSON.stringify({
                    message: request.message,
                    session_id: request.session_id,
                    include_sources: request.include_sources ?? true,
                }),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const reader = response.body?.getReader();
            const decoder = new TextDecoder();

            if (!reader) {
                throw new Error('No reader available');
            }

            while (true) {
                const { done, value } = await reader.read();

                if (done) break;

                const chunk = decoder.decode(value);
                const lines = chunk.split('\n');

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const jsonStr = line.slice(6);
                        try {
                            const data = JSON.parse(jsonStr);

                            if (data.error) {
                                onError(new Error(data.error));
                                return;
                            }

                            if (data.content && !data.is_final) {
                                onChunk(data.content);
                            }

                            if (data.is_final) {
                                onComplete(data.sources || [], data.response_time || 0);
                                return;
                            }
                        } catch (e) {
                            // Skip invalid JSON
                        }
                    }
                }
            }
        } catch (error) {
            onError(error as Error);
        }
    },

    /**
     * Get conversation history.
     */
    getHistory: async (sessionId: string, limit?: number): Promise<ChatMessage[]> => {
        const response = await apiClient.get(`/chat/history/${sessionId}`, {
            params: { limit },
        });
        return response.data.messages;
    },

    /**
     * Clear conversation history.
     */
    clearHistory: async (sessionId: string): Promise<void> => {
        await apiClient.delete(`/chat/history/${sessionId}`);
    },
};
