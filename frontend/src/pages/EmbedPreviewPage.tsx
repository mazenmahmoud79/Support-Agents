import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../hooks/useAuth';
import { MessageCircle, X, Send, Minimize2, Maximize2, Bot, ArrowLeft, Copy, Check } from 'lucide-react';
import './EmbedPreviewPage.css';

interface ChatMessage {
    role: 'user' | 'assistant';
    content: string;
}

const EmbedPreviewPage: React.FC = () => {
    const navigate = useNavigate();
    const { tenant } = useAuthStore();
    const [copied, setCopied] = useState(false);

    // Widget state
    const [widgetOpen, setWidgetOpen] = useState(false);
    const [widgetMinimized, setWidgetMinimized] = useState(false);
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [inputValue, setInputValue] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [sessionId, setSessionId] = useState<string>('');
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const baseUrl = window.location.origin.replace(':5173', ':8000');
    const slug = tenant?.slug || tenant?.name?.toLowerCase().replace(/\s+/g, '-') || 'your-slug';
    const publicApiUrl = `${baseUrl}/api/public/chat/${slug}`;

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const handleSendMessage = async () => {
        if (!inputValue.trim() || isLoading) return;

        const userMessage = inputValue.trim();
        setInputValue('');
        setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
        setIsLoading(true);

        try {
            const apiToken = tenant?.api_key;
            if (!apiToken) throw new Error('No API token');

            const response = await fetch(publicApiUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-API-Token': apiToken
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
                content: 'Connection failed. Check if backend is running.'
            }]);
        } finally {
            setIsLoading(false);
        }
    };

    const embedCode = `<!-- ${tenant?.name || 'Chat'} Widget -->
<script>
  window.CHATBOT_SLUG = '${slug}';
  window.CHATBOT_API = '${baseUrl}/api/public';
  window.CHATBOT_TOKEN = 'YOUR_API_TOKEN';
</script>
<script src="${baseUrl}/widget.js"></script>`;

    const copyEmbedCode = () => {
        navigator.clipboard.writeText(embedCode);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    return (
        <div className="embed-preview-page">
            <div className="preview-nav">
                <button className="back-btn" onClick={() => navigate('/preview')}>
                    <ArrowLeft size={20} />
                    <span>Back to Options</span>
                </button>
                <h1>Widget Preview</h1>
            </div>

            <div className="preview-content">
                {/* Browser Mockup */}
                <div className="browser-mockup">
                    <div className="browser-bar">
                        <div className="browser-dots">
                            <span className="dot red"></span>
                            <span className="dot yellow"></span>
                            <span className="dot green"></span>
                        </div>
                        <div className="browser-address">https://your-website.com</div>
                    </div>
                    <div className="browser-content">
                        <div className="placeholder-content">
                            <h2>Your Website</h2>
                            <p>This is where your website content appears.</p>
                            <p>The chat widget will appear in the bottom-right corner.</p>
                            <p className="hint">👉 Click the chat bubble to try it!</p>
                        </div>

                        {/* Chat FAB */}
                        {!widgetOpen && (
                            <button className="chat-fab" onClick={() => setWidgetOpen(true)}>
                                <MessageCircle size={24} />
                            </button>
                        )}

                        {/* Chat Widget */}
                        {widgetOpen && (
                            <div className={`chat-widget ${widgetMinimized ? 'minimized' : ''}`}>
                                <div className="widget-header">
                                    <div className="widget-title">
                                        <Bot size={20} />
                                        <span>{tenant?.name || 'Chat'}</span>
                                    </div>
                                    <div className="widget-controls">
                                        <button onClick={() => setWidgetMinimized(!widgetMinimized)}>
                                            {widgetMinimized ? <Maximize2 size={16} /> : <Minimize2 size={16} />}
                                        </button>
                                        <button onClick={() => setWidgetOpen(false)}>
                                            <X size={16} />
                                        </button>
                                    </div>
                                </div>

                                {!widgetMinimized && (
                                    <>
                                        <div className="widget-messages">
                                            {messages.length === 0 ? (
                                                <div className="welcome-message">
                                                    <Bot size={32} />
                                                    <h4>Hi there! 👋</h4>
                                                    <p>How can I help you?</p>
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
                                                placeholder="Type a message..."
                                                disabled={isLoading}
                                            />
                                            <button onClick={handleSendMessage} disabled={!inputValue.trim() || isLoading}>
                                                <Send size={18} />
                                            </button>
                                        </div>
                                    </>
                                )}
                            </div>
                        )}
                    </div>
                </div>

                {/* Embed Code Section */}
                <div className="embed-code-section">
                    <h3>📋 Embed Code</h3>
                    <p>Add this code to your website before the closing <code>&lt;/body&gt;</code> tag:</p>
                    <div className="code-box">
                        <pre>{embedCode}</pre>
                        <button className="copy-btn" onClick={copyEmbedCode}>
                            {copied ? <Check size={18} /> : <Copy size={18} />}
                            {copied ? 'Copied!' : 'Copy'}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default EmbedPreviewPage;
