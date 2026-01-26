import React, { useState, useEffect } from 'react';
import { documentService } from '../services/documentService';
import { tenantContextService } from '../services/tenantContextService';
import { Document, TenantContextUpdate, ContextOptions } from '../types';
import { FileText, Trash2, Settings, ChevronDown, ChevronUp, Save } from 'lucide-react';
import './AdminPage.css';

export const AdminPage: React.FC = () => {
    const [documents, setDocuments] = useState<Document[]>([]);
    const [loading, setLoading] = useState(true);

    // Company Settings State
    const [settingsExpanded, setSettingsExpanded] = useState(true);
    const [contextOptions, setContextOptions] = useState<ContextOptions | null>(null);
    const [contextLoading, setContextLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [saveMessage, setSaveMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

    const [formData, setFormData] = useState<TenantContextUpdate>({});

    useEffect(() => {
        loadDocuments();
        loadContext();
    }, []);

    const loadDocuments = async () => {
        try {
            const docs = await documentService.listDocuments();
            setDocuments(docs);
        } catch (error) {
            console.error('Failed to load documents:', error);
        } finally {
            setLoading(false);
        }
    };

    const loadContext = async () => {
        try {
            const [contextData, options] = await Promise.all([
                tenantContextService.getContext(),
                tenantContextService.getContextOptions()
            ]);
            setContextOptions(options);
            setFormData({
                company_name: contextData.company_name || '',
                company_description: contextData.company_description || '',
                industry: contextData.industry,
                target_audience: contextData.target_audience || '',
                tone_of_voice: contextData.tone_of_voice,
                language_style: contextData.language_style,
                response_length: contextData.response_length,
                support_email: contextData.support_email || '',
                support_phone: contextData.support_phone || '',
                support_hours: contextData.support_hours || '',
                custom_instructions: contextData.custom_instructions || '',
            });
        } catch (error) {
            console.error('Failed to load context:', error);
        } finally {
            setContextLoading(false);
        }
    };

    const handleDelete = async (id: number) => {
        if (!confirm('Delete this document?')) return;
        try {
            await documentService.deleteDocument(id);
            setDocuments((prev) => prev.filter((doc) => doc.id !== id));
        } catch (error) {
            console.error('Failed to delete:', error);
        }
    };

    const handleInputChange = (field: keyof TenantContextUpdate, value: string) => {
        setFormData(prev => ({ ...prev, [field]: value }));
    };

    const handleSaveContext = async () => {
        setSaving(true);
        setSaveMessage(null);
        try {
            await tenantContextService.updateContext(formData);
            setSaveMessage({ type: 'success', text: 'Settings saved!' });
            setTimeout(() => setSaveMessage(null), 3000);
        } catch (error) {
            console.error('Failed to save context:', error);
            setSaveMessage({ type: 'error', text: 'Failed to save.' });
        } finally {
            setSaving(false);
        }
    };

    return (
        <div className="page">
            <h1 className="page-title">Dashboard</h1>

            {/* Stats */}
            <div className="stats-grid">
                <div className="stat-card">
                    <div className="stat-label">Documents</div>
                    <div className="stat-value">{documents.length}</div>
                </div>
                <div className="stat-card">
                    <div className="stat-label">Chunks</div>
                    <div className="stat-value">
                        {documents.reduce((sum, doc) => sum + doc.chunk_count, 0)}
                    </div>
                </div>
            </div>

            {/* Company Settings */}
            <div className="section-card">
                <div
                    className="section-header"
                    onClick={() => setSettingsExpanded(!settingsExpanded)}
                >
                    <div className="section-title">
                        <Settings size={18} />
                        Company Settings
                        <span className="section-badge">AI Customization</span>
                    </div>
                    {settingsExpanded ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
                </div>

                {settingsExpanded && (
                    <div className="section-content">
                        {contextLoading ? (
                            <div className="empty-state">Loading...</div>
                        ) : (
                            <>
                                {/* Basic Info */}
                                <div className="form-section">
                                    <div className="form-section-title">Basic Info</div>
                                    <div className="form-grid">
                                        <div className="form-group">
                                            <label className="form-label">Company Name</label>
                                            <input
                                                type="text"
                                                className="form-input"
                                                value={formData.company_name || ''}
                                                onChange={(e) => handleInputChange('company_name', e.target.value)}
                                                placeholder="Your Company"
                                            />
                                        </div>
                                        <div className="form-group">
                                            <label className="form-label">Industry</label>
                                            <select
                                                className="form-select"
                                                value={formData.industry || 'other'}
                                                onChange={(e) => handleInputChange('industry', e.target.value)}
                                            >
                                                {contextOptions?.industries.map(opt => (
                                                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                                                ))}
                                            </select>
                                        </div>
                                        <div className="form-group full-width">
                                            <label className="form-label">Company Description</label>
                                            <textarea
                                                className="form-textarea"
                                                value={formData.company_description || ''}
                                                onChange={(e) => handleInputChange('company_description', e.target.value)}
                                                placeholder="Brief description of your company"
                                            />
                                        </div>
                                    </div>
                                </div>

                                {/* Response Style */}
                                <div className="form-section">
                                    <div className="form-section-title">Response Style</div>
                                    <div className="form-grid">
                                        <div className="form-group">
                                            <label className="form-label">Tone</label>
                                            <select
                                                className="form-select"
                                                value={formData.tone_of_voice || 'professional'}
                                                onChange={(e) => handleInputChange('tone_of_voice', e.target.value)}
                                            >
                                                {contextOptions?.tones.map(opt => (
                                                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                                                ))}
                                            </select>
                                        </div>
                                        <div className="form-group">
                                            <label className="form-label">Style</label>
                                            <select
                                                className="form-select"
                                                value={formData.language_style || 'conversational'}
                                                onChange={(e) => handleInputChange('language_style', e.target.value)}
                                            >
                                                {contextOptions?.language_styles.map(opt => (
                                                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                                                ))}
                                            </select>
                                        </div>
                                        <div className="form-group">
                                            <label className="form-label">Response Length</label>
                                            <select
                                                className="form-select"
                                                value={formData.response_length || 'balanced'}
                                                onChange={(e) => handleInputChange('response_length', e.target.value)}
                                            >
                                                {contextOptions?.response_lengths.map(opt => (
                                                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                                                ))}
                                            </select>
                                        </div>
                                    </div>
                                </div>

                                {/* Contact Info */}
                                <div className="form-section">
                                    <div className="form-section-title">Support Contact</div>
                                    <div className="form-grid">
                                        <div className="form-group">
                                            <label className="form-label">Email</label>
                                            <input
                                                type="email"
                                                className="form-input"
                                                value={formData.support_email || ''}
                                                onChange={(e) => handleInputChange('support_email', e.target.value)}
                                                placeholder="support@company.com"
                                            />
                                        </div>
                                        <div className="form-group">
                                            <label className="form-label">Phone</label>
                                            <input
                                                type="text"
                                                className="form-input"
                                                value={formData.support_phone || ''}
                                                onChange={(e) => handleInputChange('support_phone', e.target.value)}
                                                placeholder="+20 xxx xxx xxxx"
                                            />
                                        </div>
                                        <div className="form-group">
                                            <label className="form-label">Hours</label>
                                            <input
                                                type="text"
                                                className="form-input"
                                                value={formData.support_hours || ''}
                                                onChange={(e) => handleInputChange('support_hours', e.target.value)}
                                                placeholder="Sun-Thu 9AM-5PM"
                                            />
                                        </div>
                                    </div>
                                </div>

                                {/* Custom Instructions */}
                                <div className="form-section">
                                    <div className="form-section-title">Custom Instructions</div>
                                    <div className="form-group">
                                        <textarea
                                            className="form-textarea"
                                            value={formData.custom_instructions || ''}
                                            onChange={(e) => handleInputChange('custom_instructions', e.target.value)}
                                            placeholder="Additional instructions for the AI..."
                                            rows={3}
                                        />
                                    </div>
                                </div>

                                {/* Save */}
                                <div className="form-actions">
                                    <button
                                        onClick={handleSaveContext}
                                        disabled={saving}
                                        className="save-btn"
                                    >
                                        <Save size={16} />
                                        {saving ? 'Saving...' : 'Save Settings'}
                                    </button>
                                    {saveMessage && (
                                        <span className={`save-message ${saveMessage.type}`}>
                                            {saveMessage.text}
                                        </span>
                                    )}
                                </div>
                            </>
                        )}
                    </div>
                )}
            </div>

            {/* Documents */}
            <div className="section-card">
                <div className="section-content" style={{ paddingTop: '1.25rem' }}>
                    <h3 style={{ fontSize: '0.95rem', fontWeight: 600, marginBottom: '1rem' }}>
                        Documents ({documents.length})
                    </h3>

                    {loading ? (
                        <div className="empty-state">Loading...</div>
                    ) : documents.length === 0 ? (
                        <div className="empty-state">No documents uploaded yet.</div>
                    ) : (
                        <div>
                            {documents.map((doc) => (
                                <div key={doc.id} className="document-item">
                                    <div className="document-info">
                                        <FileText size={18} className="document-icon" />
                                        <div>
                                            <div className="document-name">{doc.filename}</div>
                                            <div className="document-meta">
                                                {doc.chunk_count} chunks
                                            </div>
                                        </div>
                                    </div>
                                    <button
                                        className="document-delete"
                                        onClick={() => handleDelete(doc.id)}
                                    >
                                        <Trash2 size={16} />
                                    </button>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};
