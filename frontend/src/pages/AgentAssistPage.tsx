/**
 * Agent Assist Page — Phase 04 E1.
 *
 * Internal panel for support agents: suggests grounded answers,
 * shows policy/process citations, flags weak-evidence cases.
 */
import React, { useState } from 'react';
import { Search, Loader2, BookOpen, AlertTriangle, ChevronDown, ChevronUp } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { chatService } from '../services/chatService';
import { SourceDocument } from '../types';
import './AgentAssistPage.css';

interface Suggestion {
    answer: string;
    sources: SourceDocument[];
    escalated: boolean;
    confidenceScore?: number;
    query: string;
}

export const AgentAssistPage: React.FC = () => {
    const [query, setQuery] = useState('');
    const [loading, setLoading] = useState(false);
    const [suggestion, setSuggestion] = useState<Suggestion | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [showSources, setShowSources] = useState(true);

    const sessionId = 'agent-assist-session';

    const handleSearch = async () => {
        if (!query.trim() || loading) return;
        setLoading(true);
        setError(null);
        setSuggestion(null);

        try {
            const resp = await chatService.sendMessage({
                message: query,
                session_id: sessionId,
                include_sources: true,
            });
            setSuggestion({
                answer: resp.response,
                sources: resp.sources ?? [],
                escalated: resp.escalated ?? false,
                confidenceScore: resp.confidence_score,
                query,
            });
        } catch (err) {
            setError('Failed to fetch suggestion. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSearch();
        }
    };

    const confidencePct = suggestion?.confidenceScore != null
        ? Math.round(suggestion.confidenceScore * 100)
        : null;

    return (
        <div className="agent-assist-page">
            <h1 className="page-title">Agent Assist</h1>
            <p className="page-subtitle">
                Look up policy, process, and FAQ answers grounded in approved knowledge.
            </p>

            {/* Search bar */}
            <div className="assist-search-bar">
                <input
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Search knowledge base (e.g. 'refund policy', 'how to reset password')"
                    disabled={loading}
                />
                <button onClick={handleSearch} disabled={!query.trim() || loading} className="assist-search-btn">
                    {loading ? <Loader2 size={18} className="spinner" /> : <Search size={18} />}
                </button>
            </div>

            {error && <div className="assist-error">{error}</div>}

            {suggestion && (
                <div className="assist-result">
                    {/* Weak evidence warning */}
                    {(suggestion.escalated || (confidencePct !== null && confidencePct < 50)) && (
                        <div className="assist-warning">
                            <AlertTriangle size={16} />
                            <span>
                                {suggestion.escalated
                                    ? 'Low confidence — this query was escalated. Verify before sharing with customer.'
                                    : `Moderate confidence (${confidencePct}%). Review sources carefully.`}
                            </span>
                        </div>
                    )}

                    {/* Answer */}
                    <div className="assist-answer-box">
                        <div className="assist-answer-label">
                            Suggested Answer
                            {confidencePct !== null && (
                                <span className={`assist-confidence ${confidencePct >= 70 ? 'high' : confidencePct >= 45 ? 'medium' : 'low'}`}>
                                    {confidencePct}% confidence
                                </span>
                            )}
                        </div>
                        <div className="assist-answer-content">
                            <ReactMarkdown>{suggestion.answer}</ReactMarkdown>
                        </div>
                    </div>

                    {/* Source citations */}
                    {suggestion.sources.length > 0 && (
                        <div className="assist-sources">
                            <button
                                className="assist-sources-toggle"
                                onClick={() => setShowSources((s) => !s)}
                            >
                                <BookOpen size={15} />
                                {suggestion.sources.length} source{suggestion.sources.length !== 1 ? 's' : ''}
                                {showSources ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
                            </button>

                            {showSources && (
                                <div className="assist-sources-list">
                                    {suggestion.sources.map((src, idx) => (
                                        <div key={idx} className="assist-source-card">
                                            <div className="assist-source-header">
                                                <span className="assist-source-num">
                                                    [{src.source_number ?? idx + 1}]
                                                </span>
                                                <span className="assist-source-filename">{src.filename}</span>
                                                {src.page_number && (
                                                    <span className="assist-source-page">p.{src.page_number}</span>
                                                )}
                                                <span className="assist-source-score">
                                                    {(src.relevance_score * 100).toFixed(0)}% relevant
                                                </span>
                                            </div>
                                            {src.section_title && (
                                                <div className="assist-source-section">{src.section_title}</div>
                                            )}
                                            {src.snippet && (
                                                <p className="assist-source-snippet">{src.snippet}</p>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default AgentAssistPage;
