import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../hooks/useAuth';
import { Globe, Layout, ChevronRight, ExternalLink, Sparkles } from 'lucide-react';
import './PreviewChoicePage.css';

const PreviewChoicePage: React.FC = () => {
    const navigate = useNavigate();
    const { tenant } = useAuthStore();

    return (
        <div className="preview-choice-page">
            <div className="choice-header">
                <h1>🎯 Preview Your Chatbot</h1>
                <p>Choose how you want to integrate your AI chatbot</p>
            </div>

            <div className="choice-cards">
                {/* Option 1: Has a Website */}
                <div
                    className="choice-card"
                    onClick={() => navigate('/preview/embed')}
                >
                    <div className="choice-icon has-website">
                        <Globe size={32} />
                    </div>
                    <h2>I Have a Website</h2>
                    <p>
                        Embed the chatbot widget on your existing website.
                        See how it looks in the bottom-right corner of any page.
                    </p>
                    <ul className="choice-features">
                        <li>✓ Floating chat widget</li>
                        <li>✓ Easy embed code</li>
                        <li>✓ Works on any website</li>
                    </ul>
                    <div className="choice-action">
                        <span>Preview Widget</span>
                        <ChevronRight size={20} />
                    </div>
                </div>

                {/* Option 2: No Website */}
                <div
                    className="choice-card featured"
                    onClick={() => navigate('/preview/hosted')}
                >
                    <div className="featured-badge">
                        <Sparkles size={14} />
                        <span>Recommended</span>
                    </div>
                    <div className="choice-icon no-website">
                        <Layout size={32} />
                    </div>
                    <h2>I Need a Website</h2>
                    <p>
                        Get a ready-to-use landing page for your business with
                        the chatbot built in. No coding required!
                    </p>
                    <ul className="choice-features">
                        <li>✓ Professional landing page</li>
                        <li>✓ Your company branding</li>
                        <li>✓ Instant deployment</li>
                        <li>✓ Share link with customers</li>
                    </ul>
                    <div className="choice-action">
                        <span>Preview Landing Page</span>
                        <ChevronRight size={20} />
                    </div>
                </div>
            </div>

            <div className="choice-footer">
                <p>
                    <strong>Company:</strong> {tenant?.name || 'Your Company'}
                </p>
                <p className="hint">
                    Don't worry, you can always switch between options later!
                </p>
            </div>
        </div>
    );
};

export default PreviewChoicePage;
