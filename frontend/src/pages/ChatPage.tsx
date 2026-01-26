import React from 'react';
import { ChatInterface } from '../components/chat/ChatInterface';

export const ChatPage: React.FC = () => {
    return (
        <div className="page">
            <h1 className="page-title">💬 Chat with AI Assistant</h1>
            <ChatInterface />
        </div>
    );
};
