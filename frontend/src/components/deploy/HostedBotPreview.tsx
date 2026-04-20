import React, { useState, useRef, useEffect } from 'react';
import { useAuthStore } from '../../hooks/useAuth';
import { tenantContextService } from '../../services/tenantContextService';
import { TenantContext } from '../../types';
import { MessageCircle, X, Send, Bot, Copy, Check, Phone, Mail, Globe, Clock } from 'lucide-react';

interface ChatMessage {
    role: 'user' | 'assistant';
    content: string;
}

const HostedBotPreview: React.FC = () => {
    const { tenant } = useAuthStore();
    const [context, setContext] = useState<TenantContext | null>(null);
    const [loading, setLoading] = useState(true);
    const [copied, setCopied] = useState(false);

    // Chat state
    const [chatOpen, setChatOpen] = useState(false);
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [inputValue, setInputValue] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [sessionId, setSessionId] = useState<string>('');
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const baseUrl = window.location.origin.replace(':5173', ':8000');
    const slug = tenant?.slug || tenant?.name?.toLowerCase().replace(/\s+/g, '-') || 'demo';
    const publicApiUrl = `${baseUrl}/api/public/chat/${slug}`;
    const hostedUrl = `${window.location.origin}/page/${slug}`;

    useEffect(() => {
        loadContext();
    }, []);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const loadContext = async () => {
        try {
            const data = await tenantContextService.getContext();
            setContext(data);
        } catch (error) {
            console.error('Failed to load context:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleSendMessage = async () => {
        if (!inputValue.trim() || isLoading) return;

        const userMessage = inputValue.trim();
        setInputValue('');
        setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
        setIsLoading(true);

        try {
            // Use tenant api_key for the public chat preview
            const tokenToUse = tenant?.api_key;
            if (!tokenToUse) throw new Error('No API token');

            const response = await fetch(publicApiUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-API-Token': tokenToUse
                },
                body: JSON.stringify({
                    message: userMessage,
                    session_id: sessionId || undefined
                })
            });

            if (!response.ok) throw new Error('Failed');

            const data = await response.json();
            setSessionId(data.session_id);
            setMessages(prev => [...prev, { role: 'assistant', content: data.response }]);
        } catch (error) {
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: 'Connection failed. Please try again.'
            }]);
        } finally {
            setIsLoading(false);
        }
    };

    const copyLink = () => {
        navigator.clipboard.writeText(hostedUrl);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    const companyName = context?.company_name || tenant?.name || 'Your Company';
    const description = context?.company_description || 'We provide excellent customer service powered by AI.';
    const industry = context?.industry?.replace(/_/g, ' ') || 'Technology';

    if (loading) {
        return <div className="loading">Loading your preview...</div>;
    }

    return (
        <div className="hosted-bot-preview">
            <div className="preview-header">
                <div className="share-section">
                    <span className="share-label">Your Page URL:</span>
                    <div className="share-url">
                        <code>{hostedUrl}</code>
                        <button onClick={copyLink}>
                            {copied ? <Check size={16} /> : <Copy size={16} />}
                        </button>
                    </div>
                </div>
            </div>

            {/* Landing Page Preview */}
            <div className="landing-preview">
                <div className="landing-page">
                    {/* Hero Section */}
                    <section className="hero">
                        <div className="hero-content">
                            <div className="hero-badge">{industry}</div>
                            <h1>{companyName}</h1>
                            <p>{description}</p>
                            <button className="hero-cta" onClick={() => setChatOpen(true)}>
                                <MessageCircle size={20} />
                                Chat with Us
                            </button>
                        </div>
                        <div className="hero-visual">
                            <div className="visual-card">
                                <Bot size={48} />
                                <span>AI-Powered Support</span>
                            </div>
                        </div>
                    </section>

                    {/* Features Section */}
                    <section className="features">
                        <h2>Why Choose Us?</h2>
                        <div className="features-grid">
                            <div className="feature-card">
                                <div className="feature-icon">⚡</div>
                                <h3>Instant Responses</h3>
                                <p>Get answers in seconds, 24/7</p>
                            </div>
                            <div className="feature-card">
                                <div className="feature-icon">🎯</div>
                                <h3>Accurate Information</h3>
                                <p>AI trained on our knowledge base</p>
                            </div>
                            <div className="feature-card">
                                <div className="feature-icon">🤝</div>
                                <h3>Friendly Service</h3>
                                <p>Always ready to help</p>
                            </div>
                        </div>
                    </section>

                    {/* Contact Section */}
                    {(context?.support_email || context?.support_phone || context?.support_hours) && (
                        <section className="contact">
                            <h2>Contact Us</h2>
                            <div className="contact-grid">
                                {context?.support_email && (
                                    <div className="contact-item">
                                        <Mail size={20} />
                                        <span>{context.support_email}</span>
                                    </div>
                                )}
                                {context?.support_phone && (
                                    <div className="contact-item">
                                        <Phone size={20} />
                                        <span>{context.support_phone}</span>
                                    </div>
                                )}
                                {context?.support_hours && (
                                    <div className="contact-item">
                                        <Clock size={20} />
                                        <span>{context.support_hours}</span>
                                    </div>
                                )}
                                {context?.support_url && (
                                    <div className="contact-item">
                                        <Globe size={20} />
                                        <span>{context.support_url}</span>
                                    </div>
                                )}
                            </div>
                        </section>
                    )}

                    {/* Footer */}
                    <footer className="landing-footer">
                        <p>© {new Date().getFullYear()} {companyName}. Powered by AI Support Agent.</p>
                    </footer>

                    {/* Chat FAB */}
                    {!chatOpen && (
                        <button className="chat-fab" onClick={() => setChatOpen(true)}>
                            <MessageCircle size={24} />
                        </button>
                    )}

                    {/* Chat Widget */}
                    {chatOpen && (
                        <div className="chat-widget">
                            <div className="widget-header">
                                <div className="widget-title">
                                    <Bot size={20} />
                                    <span>{companyName}</span>
                                </div>
                                <button onClick={() => setChatOpen(false)}>
                                    <X size={18} />
                                </button>
                            </div>
                            <div className="widget-messages">
                                {messages.length === 0 ? (
                                    <div className="welcome-message">
                                        <Bot size={36} />
                                        <h4>Welcome to {companyName}! 👋</h4>
                                        <p>How can we help you today?</p>
                                    </div>
                                ) : (
                                    messages.map((msg, idx) => (
                                        <div key={idx} className={`message ${msg.role}`}>
                                            <div className="message-content">{msg.content}</div>
                                        </div>
                                    ))
                                )}
                                {isLoading && (
                                    <div className="message assistant">
                                        <div className="message-content typing">
                                            <span></span><span></span><span></span>
                                        </div>
                                    </div>
                                )}
                                <div ref={messagesEndRef} />
                            </div>
                            <div className="widget-input">
                                <input
                                    value={inputValue}
                                    onChange={(e) => setInputValue(e.target.value)}
                                    onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                                    placeholder="Type your message..."
                                    disabled={isLoading}
                                />
                                <button onClick={handleSendMessage} disabled={!inputValue.trim() || isLoading}>
                                    <Send size={18} />
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default HostedBotPreview;
