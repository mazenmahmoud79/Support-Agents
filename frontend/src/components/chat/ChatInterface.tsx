import React, { useState, useRef, useEffect } from 'react';
import { Send, Loader2 } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { chatService } from '../../services/chatService';
import { SourceDocument } from '../../types';
import './ChatInterface.css';

interface Message {
    role: 'user' | 'assistant';
    content: string;
    sources?: SourceDocument[];
    timestamp: Date;
}

export const ChatInterface: React.FC = () => {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [sessionId] = useState(() => `session_${Date.now()}`);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(scrollToBottom, [messages]);

    const handleSend = async () => {
        if (!input.trim() || isLoading) return;

        const userMessage: Message = {
            role: 'user',
            content: input,
            timestamp: new Date(),
        };

        setMessages((prev) => [...prev, userMessage]);
        setInput('');
        setIsLoading(true);

        const assistantMessageIndex = messages.length + 1;
        setMessages((prev) => [
            ...prev,
            {
                role: 'assistant',
                content: '',
                timestamp: new Date(),
            },
        ]);

        try {
            await chatService.sendMessageStream(
                {
                    message: input,
                    session_id: sessionId,
                    include_sources: true,
                },
                (chunk) => {
                    setMessages((prev) => {
                        const newMessages = [...prev];
                        newMessages[assistantMessageIndex] = {
                            ...newMessages[assistantMessageIndex],
                            content: newMessages[assistantMessageIndex].content + chunk,
                        };
                        return newMessages;
                    });
                },
                (sources) => {
                    setMessages((prev) => {
                        const newMessages = [...prev];
                        newMessages[assistantMessageIndex] = {
                            ...newMessages[assistantMessageIndex],
                            sources,
                        };
                        return newMessages;
                    });
                    setIsLoading(false);
                },
                (error) => {
                    console.error('Chat error:', error);
                    setMessages((prev) => {
                        const newMessages = [...prev];
                        newMessages[assistantMessageIndex] = {
                            role: 'assistant',
                            content: 'Sorry, an error occurred. Please try again.',
                            timestamp: new Date(),
                        };
                        return newMessages;
                    });
                    setIsLoading(false);
                }
            );
        } catch (error) {
            console.error('Send failed:', error);
            setIsLoading(false);
        }
    };

    const handleKeyPress = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    return (
        <div className="chat-container">
            <div className="messages-container">
                {messages.length === 0 ? (
                    <div className="empty-state">
                        <h2>How can I help you?</h2>
                        <p>Ask me anything about your knowledge base.</p>
                    </div>
                ) : (
                    messages.map((msg, idx) => (
                        <div key={idx} className={`message message-${msg.role}`}>
                            <div className="message-content">
                                {msg.content ? (
                                    msg.role === 'assistant' ? (
                                        <ReactMarkdown
                                            components={{
                                                code({ node, className, children, ...props }) {
                                                    const isInline = !className;
                                                    return isInline ? (
                                                        <code className="inline-code" {...props}>
                                                            {children}
                                                        </code>
                                                    ) : (
                                                        <code className={className} {...props}>
                                                            {children}
                                                        </code>
                                                    );
                                                },
                                                pre({ children }) {
                                                    return <pre className="code-block">{children}</pre>;
                                                },
                                            }}
                                        >
                                            {msg.content}
                                        </ReactMarkdown>
                                    ) : (
                                        msg.content
                                    )
                                ) : (
                                    isLoading && idx === messages.length - 1 && (
                                        <div className="typing-indicator">
                                            <span></span>
                                            <span></span>
                                            <span></span>
                                        </div>
                                    )
                                )}
                            </div>
                            {msg.sources && msg.sources.length > 0 && (
                                <div className="sources">
                                    <span className="sources-title">Sources:</span>
                                    {msg.sources.map((source, sidx) => (
                                        <span key={sidx} className="source-item">
                                            {source.filename}
                                        </span>
                                    ))}
                                </div>
                            )}
                        </div>
                    ))
                )}
                <div ref={messagesEndRef} />
            </div>

            <div className="input-container">
                <textarea
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="Type your message..."
                    disabled={isLoading}
                    rows={1}
                />
                <button
                    onClick={handleSend}
                    disabled={!input.trim() || isLoading}
                    className="send-btn"
                >
                    {isLoading ? <Loader2 size={18} className="spinner" /> : <Send size={18} />}
                </button>
            </div>
        </div>
    );
};
