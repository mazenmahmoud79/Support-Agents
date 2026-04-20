import React, { useState, useRef, useEffect } from 'react';
import { Send, Loader2, ThumbsUp, ThumbsDown, AlertTriangle, BookOpen, ChevronDown, ChevronUp, Phone } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { chatService } from '../../services/chatService';
import { feedbackService } from '../../services/feedbackService';
import { SourceDocument, FeedbackType } from '../../types';
import './ChatInterface.css';

interface Message {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    sources?: SourceDocument[];
    timestamp: Date;
    escalated?: boolean;
    confidenceScore?: number;
    feedback?: 'up' | 'down' | null;
    showSources?: boolean;
}

/** Detect if a string is predominantly Arabic/RTL. */
function detectDirection(text: string): 'rtl' | 'ltr' {
    const arabicChars = (text.match(/[\u0600-\u06ff]/g) || []).length;
    return arabicChars / Math.max(text.length, 1) > 0.2 ? 'rtl' : 'ltr';
}

export const ChatInterface: React.FC = () => {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [sessionId] = useState(() => `session_${Date.now()}`);
    const [correctionTarget, setCorrectionTarget] = useState<string | null>(null);
    const [correctionText, setCorrectionText] = useState('');
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(scrollToBottom, [messages]);

    const handleSend = async () => {
        if (!input.trim() || isLoading) return;

        const userMsg: Message = {
            id: `user_${Date.now()}`,
            role: 'user',
            content: input,
            timestamp: new Date(),
        };

        const assistantId = `asst_${Date.now()}`;
        const assistantMsg: Message = {
            id: assistantId,
            role: 'assistant',
            content: '',
            timestamp: new Date(),
            showSources: false,
        };

        setMessages((prev) => [...prev, userMsg, assistantMsg]);
        const assistantIndex = messages.length + 1;
        setInput('');
        setIsLoading(true);

        try {
            await chatService.sendMessageStream(
                { message: input, session_id: sessionId, include_sources: true },
                (chunk) => {
                    setMessages((prev) => {
                        const next = [...prev];
                        const target = next[assistantIndex];
                        if (target) {
                            next[assistantIndex] = { ...target, content: target.content + chunk };
                        }
                        return next;
                    });
                },
                (sources, _responseTime, escalated, confidenceScore) => {
                    setMessages((prev) => {
                        const next = [...prev];
                        const target = next[assistantIndex];
                        if (target) {
                            next[assistantIndex] = {
                                ...target,
                                sources,
                                escalated: escalated ?? false,
                                confidenceScore,
                            };
                        }
                        return next;
                    });
                    setIsLoading(false);
                },
                (error) => {
                    console.error('Chat error:', error);
                    setMessages((prev) => {
                        const next = [...prev];
                        if (next[assistantIndex]) {
                            next[assistantIndex] = {
                                ...next[assistantIndex],
                                content: 'Sorry, an error occurred. Please try again.',
                            };
                        }
                        return next;
                    });
                    setIsLoading(false);
                }
            );
        } catch (error) {
            console.error('Send failed:', error);
            setIsLoading(false);
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    const handleFeedback = async (msg: Message, type: 'up' | 'down') => {
        if (msg.feedback) return; // already voted
        setMessages((prev) =>
            prev.map((m) => (m.id === msg.id ? { ...m, feedback: type } : m))
        );
        await feedbackService.submitFeedback({
            session_id: sessionId,
            message_id: msg.id,
            feedback_type: type === 'up' ? FeedbackType.THUMBS_UP : FeedbackType.THUMBS_DOWN,
            query: messages[messages.findIndex((m) => m.id === msg.id) - 1]?.content,
            response: msg.content,
            source_documents: msg.sources,
        }).catch(console.error);
    };

    const toggleSources = (msgId: string) => {
        setMessages((prev) =>
            prev.map((m) => (m.id === msgId ? { ...m, showSources: !m.showSources } : m))
        );
    };

    const submitCorrection = async (msg: Message) => {
        if (!correctionText.trim()) return;
        const originalQuery =
            messages[messages.findIndex((m) => m.id === msg.id) - 1]?.content || '';
        await feedbackService.submitCorrection({
            session_id: sessionId,
            message_id: msg.id,
            original_query: originalQuery,
            original_response: msg.content,
            corrected_response: correctionText,
        }).catch(console.error);
        setCorrectionTarget(null);
        setCorrectionText('');
    };

    return (
        <div className="chat-interface">
            <div className="chat-header">
                <div className="chat-bot-avatar">Z</div>
                <div className="chat-header-info">
                    <h3>Zada AI</h3>
                    <span className="chat-status">Online</span>
                </div>
            </div>

            <div className="chat-messages">
                {messages.length === 0 ? (
                    <div className="chat-empty">
                        <div className="chat-empty-icon">
                            <Send size={24} />
                        </div>
                        <h3>How can I help you?</h3>
                        <p>Ask me anything about your knowledge base.</p>
                    </div>
                ) : (
                    messages.map((msg, idx) => {
                        const dir = detectDirection(msg.content);
                        return (
                            <div key={msg.id} className={`message-group ${msg.role === 'assistant' ? 'bot' : 'user'}`}>
                                {/* Escalation Banner */}
                                {msg.role === 'assistant' && msg.escalated && (
                                    <div className="escalation-banner">
                                        <AlertTriangle size={16} />
                                        <span>
                                            I wasn't confident enough to answer this. A human agent
                                            can help you better.
                                        </span>
                                        <a
                                            href="mailto:support@example.com"
                                            className="escalation-link"
                                        >
                                            <Phone size={14} /> Contact Support
                                        </a>
                                    </div>
                                )}

                                <div className={`message-row ${msg.role === 'assistant' ? 'bot' : 'user'}`}>
                                {msg.role === 'assistant' && (
                                    <div className="message-avatar bot">Z</div>
                                )}

                                {/* Message Bubble */}
                                <div className="message-bubble" dir={dir}>
                                    {msg.content ? (
                                        msg.role === 'assistant' ? (
                                            <ReactMarkdown
                                                components={{
                                                    code({ className, children, ...props }) {
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
                                                        return (
                                                            <pre className="code-block">{children}</pre>
                                                        );
                                                    },
                                                }}
                                            >
                                                {msg.content}
                                            </ReactMarkdown>
                                        ) : (
                                            msg.content
                                        )
                                    ) : (
                                        isLoading &&
                                        idx === messages.length - 1 && (
                                            <div className="typing-dots">
                                                <div className="typing-dot" />
                                                <div className="typing-dot" />
                                                <div className="typing-dot" />
                                            </div>
                                        )
                                    )}
                                </div>

                                {msg.role === 'user' && (
                                    <div className="message-avatar user-av">U</div>
                                )}
                                </div>{/* end message-row */}

                                {/* Feedback buttons */}
                                {msg.role === 'assistant' && msg.content && (
                                    <div className="message-actions">
                                        <button
                                            className={`feedback-btn ${msg.feedback === 'up' ? 'active-up' : ''}`}
                                            title="Helpful"
                                            onClick={() => handleFeedback(msg, 'up')}
                                            disabled={!!msg.feedback}
                                        >
                                            <ThumbsUp size={14} />
                                        </button>
                                        <button
                                            className={`feedback-btn ${msg.feedback === 'down' ? 'active-down' : ''}`}
                                            title="Not helpful"
                                            onClick={() => handleFeedback(msg, 'down')}
                                            disabled={!!msg.feedback}
                                        >
                                            <ThumbsDown size={14} />
                                        </button>
                                        <button
                                            className="feedback-btn correct-btn"
                                            title="Suggest correction"
                                            onClick={() =>
                                                setCorrectionTarget(
                                                    correctionTarget === msg.id ? null : msg.id
                                                )
                                            }
                                        >
                                            ✏️
                                        </button>

                                        {/* Citations toggle (D1) */}
                                        {msg.sources && msg.sources.length > 0 && (
                                            <button
                                                className="sources-toggle-btn"
                                                onClick={() => toggleSources(msg.id)}
                                            >
                                                <BookOpen size={14} />
                                                {msg.sources.length} source
                                                {msg.sources.length !== 1 ? 's' : ''}
                                                {msg.showSources ? (
                                                    <ChevronUp size={12} />
                                                ) : (
                                                    <ChevronDown size={12} />
                                                )}
                                            </button>
                                        )}
                                    </div>
                                )}

                                {/* Agent correction modal (B4) */}
                                {correctionTarget === msg.id && (
                                    <div className="correction-modal">
                                        <p className="correction-label">Suggest a correction:</p>
                                        <textarea
                                            value={correctionText}
                                            onChange={(e) => setCorrectionText(e.target.value)}
                                            placeholder="Write the correct answer..."
                                            rows={3}
                                        />
                                        <div className="correction-actions">
                                            <button
                                                className="correction-submit"
                                                onClick={() => submitCorrection(msg)}
                                            >
                                                Submit
                                            </button>
                                            <button
                                                className="correction-cancel"
                                                onClick={() => setCorrectionTarget(null)}
                                            >
                                                Cancel
                                            </button>
                                        </div>
                                    </div>
                                )}

                                {/* Source citation cards (D1) */}
                                {msg.showSources && msg.sources && msg.sources.length > 0 && (
                                    <div className="sources-panel">
                                        {msg.sources.map((src, sidx) => (
                                            <div key={sidx} className="source-card">
                                                <div className="source-card-header">
                                                    <span className="source-number">
                                                        [{src.source_number ?? sidx + 1}]
                                                    </span>
                                                    <span className="source-filename">
                                                        {src.filename}
                                                    </span>
                                                    {src.page_number && (
                                                        <span className="source-page">
                                                            p.{src.page_number}
                                                        </span>
                                                    )}
                                                </div>
                                                {src.section_title && (
                                                    <div className="source-section">
                                                        {src.section_title}
                                                    </div>
                                                )}
                                                {src.snippet && (
                                                    <p className="source-snippet">{src.snippet}</p>
                                                )}
                                                <div className="source-score">
                                                    Relevance:{' '}
                                                    {(src.relevance_score * 100).toFixed(0)}%
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        );
                    })
                )}
                <div ref={messagesEndRef} />
            </div>

            <div className="chat-input-bar">
                <textarea
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Type your message..."
                    disabled={isLoading}
                    rows={1}
                    className="chat-input"
                    dir={detectDirection(input)}
                />
                <button
                    onClick={handleSend}
                    disabled={!input.trim() || isLoading}
                    className="chat-send-btn"
                >
                    {isLoading ? (
                        <Loader2 size={18} className="spinner" />
                    ) : (
                        <Send size={18} />
                    )}
                </button>
            </div>
        </div>
    );
};

