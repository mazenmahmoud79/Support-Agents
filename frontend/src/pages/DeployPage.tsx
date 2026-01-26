import React, { useState } from 'react';
import { ArrowLeft, Globe, Layout, ChevronRight, Sparkles } from 'lucide-react';
import IntegrationGuide from '../components/deploy/IntegrationGuide';
import HostedBotPreview from '../components/deploy/HostedBotPreview';
import './DeployPage.css';

type ViewMode = 'selection' | 'integration' | 'preview';

const DeployPage: React.FC = () => {
    const [view, setView] = useState<ViewMode>('selection');

    if (view === 'integration') {
        return (
            <div className="deploy-page">
                <button className="back-btn" onClick={() => setView('selection')}>
                    <ArrowLeft size={20} />
                    <span>Back to Options</span>
                </button>
                <IntegrationGuide />
            </div>
        );
    }

    if (view === 'preview') {
        return (
            <div className="deploy-page">
                <button className="back-btn" onClick={() => setView('selection')}>
                    <ArrowLeft size={20} />
                    <span>Back to Options</span>
                </button>
                <HostedBotPreview />
            </div>
        );
    }

    return (
        <div className="deploy-page">
            <div className="choice-header">
                <h1>🚀 Deploy Your Chatbot</h1>
                <p>Do you already have a website, or do you need one?</p>
            </div>

            <div className="choice-cards">
                {/* Option 1: Has Website */}
                <div className="choice-card" onClick={() => setView('integration')}>
                    <div className="choice-icon has-website">
                        <Globe size={32} />
                    </div>
                    <h2>I Have a Website</h2>
                    <p>Get the integration code and API keys to add the chatbot to your existing site.</p>
                    <ul className="choice-features">
                        <li>✓ Javascript Snippets</li>
                        <li>✓ API Documentation</li>
                        <li>✓ React/Widget Support</li>
                    </ul>
                    <div className="choice-action">
                        <span>Get Integration Code</span>
                        <ChevronRight size={20} />
                    </div>
                </div>

                {/* Option 2: No Website */}
                <div className="choice-card featured" onClick={() => setView('preview')}>
                    <div className="featured-badge">
                        <Sparkles size={14} />
                        <span>Recommended</span>
                    </div>
                    <div className="choice-icon no-website">
                        <Layout size={32} />
                    </div>
                    <h2>I Need a Website</h2>
                    <p>We've created a professional landing page for you with the chatbot built-in.</p>
                    <ul className="choice-features">
                        <li>✓ Instant Landing Page</li>
                        <li>✓ SEO Ready</li>
                        <li>✓ Zero Coding Required</li>
                    </ul>
                    <div className="choice-action">
                        <span>View Landing Page</span>
                        <ChevronRight size={20} />
                    </div>
                </div>
            </div>
        </div>
    );
};

export default DeployPage;
