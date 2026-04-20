import React, { useState, useEffect } from 'react';
import { useAuthStore } from '../../hooks/useAuth';
import { tenantContextService, TokenInfo } from '../../services/tenantContextService';
import { Key, RefreshCw, Copy, Check, Eye, EyeOff } from 'lucide-react';

const IntegrationGuide: React.FC = () => {
    const { tenant } = useAuthStore();
    const [copied, setCopied] = useState<string | null>(null);
    const [activeTab, setActiveTab] = useState('javascript');

    // Token state
    const [tokenInfo, setTokenInfo] = useState<TokenInfo | null>(null);
    const [newToken, setNewToken] = useState<string | null>(null);
    const [showToken, setShowToken] = useState(false);
    const [regenerating, setRegenerating] = useState(false);

    const baseUrl = window.location.origin.replace(':5173', ':8000');
    const slug = tenant?.slug || tenant?.name?.toLowerCase().replace(/\s+/g, '-') || 'your-slug';
    const publicApiUrl = `${baseUrl}/api/public/chat/${slug}`;
    const streamApiUrl = `${baseUrl}/api/public/chat/${slug}/stream`;

    useEffect(() => {
        loadTokenInfo();
    }, []);

    const loadTokenInfo = async () => {
        try {
            const info = await tenantContextService.getTokenInfo();
            setTokenInfo(info);
        } catch (error) {
            console.error('Failed to load token info:', error);
        }
    };

    const handleRegenerateToken = async () => {
        if (!confirm('This will invalidate your current token. Continue?')) return;

        setRegenerating(true);
        try {
            const result = await tenantContextService.regenerateToken();
            setNewToken(result.api_key);
            setShowToken(true);
        } catch (error) {
            console.error('Failed to regenerate token:', error);
        } finally {
            setRegenerating(false);
        }
    };

    const copyToClipboard = (text: string, id: string) => {
        navigator.clipboard.writeText(text);
        setCopied(id);
        setTimeout(() => setCopied(null), 2000);
    };

    const dismissToken = () => {
        if (confirm('Make sure you have copied the token. Continue?')) {
            setNewToken(null);
            loadTokenInfo();
        }
    };

    const codeExamples: Record<string, string> = {
        javascript: `const response = await fetch('${publicApiUrl}', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-API-Token': 'YOUR_TOKEN'
  },
  body: JSON.stringify({ message: 'Hello' })
});
const data = await response.json();`,

        curl: `curl -X POST "${publicApiUrl}" \\
  -H "Content-Type: application/json" \\
  -H "X-API-Token: YOUR_TOKEN" \\
  -d '{"message": "Hello"}'`,

        widget: `<script>
  window.CHATBOT_SLUG = '${slug}';
  window.CHATBOT_API = '${baseUrl}/api/public';
  window.CHATBOT_TOKEN = 'YOUR_TOKEN';
</script>
<script src="${baseUrl}/widget.js"></script>`
    };

    return (
        <div className="integration-guide">
            <div className="guide-header">
                <h2>Integration Steps</h2>
                <p>Follow these steps to integrate the chatbot into your website.</p>
            </div>

            {/* API Token */}
            <section className="section">
                <div className="section-header">
                    <Key size={18} />
                    <h3>API Token</h3>
                </div>

                {newToken ? (
                    <div className="token-new">
                        <p className="token-warning">⚠️ Copy this token now. It won't be shown again.</p>
                        <div className="token-box">
                            <code>{showToken ? newToken : '•'.repeat(32)}</code>
                            <div className="token-actions">
                                <button onClick={() => setShowToken(!showToken)}>
                                    {showToken ? <EyeOff size={16} /> : <Eye size={16} />}
                                </button>
                                <button onClick={() => copyToClipboard(newToken, 'token')}>
                                    {copied === 'token' ? <Check size={16} /> : <Copy size={16} />}
                                </button>
                            </div>
                        </div>
                        <button onClick={dismissToken} className="btn-text">
                            I've saved it — dismiss
                        </button>
                    </div>
                ) : (
                    <div className="token-current">
                        <div className="token-preview">
                            <span>Current:</span>
                            <code>{tokenInfo?.token_preview || '...'}</code>
                        </div>
                        <button
                            onClick={handleRegenerateToken}
                            disabled={regenerating}
                            className="btn-secondary"
                        >
                            <RefreshCw size={16} className={regenerating ? 'spin' : ''} />
                            {regenerating ? 'Generating...' : 'Generate New'}
                        </button>
                    </div>
                )}
            </section>

            {/* API Endpoints */}
            <section className="section">
                <h3>API Endpoints</h3>
                <div className="endpoints">
                    <div className="endpoint">
                        <span className="method">POST</span>
                        <code>{publicApiUrl}</code>
                        <button onClick={() => copyToClipboard(publicApiUrl, 'url1')}>
                            {copied === 'url1' ? <Check size={14} /> : <Copy size={14} />}
                        </button>
                    </div>
                    <div className="endpoint">
                        <span className="method">POST</span>
                        <code>{streamApiUrl}</code>
                        <button onClick={() => copyToClipboard(streamApiUrl, 'url2')}>
                            {copied === 'url2' ? <Check size={14} /> : <Copy size={14} />}
                        </button>
                    </div>
                </div>
            </section>

            {/* Code Examples */}
            <section className="section">
                <h3>Code Examples</h3>
                <div className="tabs">
                    {Object.keys(codeExamples).map(tab => (
                        <button
                            key={tab}
                            className={`tab ${activeTab === tab ? 'active' : ''}`}
                            onClick={() => setActiveTab(tab)}
                        >
                            {tab.charAt(0).toUpperCase() + tab.slice(1)}
                        </button>
                    ))}
                </div>
                <div className="code-block">
                    <pre>{codeExamples[activeTab]}</pre>
                    <button
                        className="copy-btn"
                        onClick={() => copyToClipboard(codeExamples[activeTab], 'code')}
                    >
                        {copied === 'code' ? <Check size={14} /> : <Copy size={14} />}
                        {copied === 'code' ? 'Copied' : 'Copy'}
                    </button>
                </div>
            </section>
        </div>
    );
};

export default IntegrationGuide;
