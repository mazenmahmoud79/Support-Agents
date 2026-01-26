import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    Users, FileText, Plus, Copy, Check, Trash2,
    ToggleLeft, ToggleRight, LogOut, RefreshCw
} from 'lucide-react';
import { superAdminService, TenantInfo, AdminStats } from '../services/superAdminService';
import './SuperAdminPage.css';

const SuperAdminPage: React.FC = () => {
    const navigate = useNavigate();
    const [stats, setStats] = useState<AdminStats | null>(null);
    const [tenants, setTenants] = useState<TenantInfo[]>([]);
    const [loading, setLoading] = useState(true);
    const [copiedId, setCopiedId] = useState<string | null>(null);

    // Create tenant modal
    const [showModal, setShowModal] = useState(false);
    const [newTenantName, setNewTenantName] = useState('');
    const [creating, setCreating] = useState(false);

    useEffect(() => {
        if (!superAdminService.isAuthenticated()) {
            navigate('/super-admin');
            return;
        }
        loadData();
    }, [navigate]);

    const loadData = async () => {
        setLoading(true);
        try {
            const [statsData, tenantsData] = await Promise.all([
                superAdminService.getStats(),
                superAdminService.listTenants()
            ]);
            setStats(statsData);
            setTenants(tenantsData.tenants);
        } catch (error) {
            console.error('Failed to load data:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleCopyDemoId = (demoId: string) => {
        navigator.clipboard.writeText(demoId);
        setCopiedId(demoId);
        setTimeout(() => setCopiedId(null), 2000);
    };

    const handleToggleActive = async (tenant: TenantInfo) => {
        try {
            await superAdminService.updateTenant(tenant.tenant_id, {
                is_active: !tenant.is_active
            });
            loadData();
        } catch (error) {
            console.error('Failed to update tenant:', error);
        }
    };

    const handleDelete = async (tenant: TenantInfo) => {
        if (!confirm(`Delete "${tenant.name}"? This will deactivate the tenant.`)) return;

        try {
            await superAdminService.deleteTenant(tenant.tenant_id);
            loadData();
        } catch (error) {
            console.error('Failed to delete tenant:', error);
        }
    };

    const handleCreateTenant = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!newTenantName.trim()) return;

        setCreating(true);
        try {
            await superAdminService.createTenant(newTenantName.trim());
            setNewTenantName('');
            setShowModal(false);
            loadData();
        } catch (error) {
            console.error('Failed to create tenant:', error);
        } finally {
            setCreating(false);
        }
    };

    const handleLogout = () => {
        superAdminService.clearAuth();
        navigate('/super-admin');
    };

    if (loading) {
        return (
            <div className="super-admin-page">
                <div className="loading">Loading...</div>
            </div>
        );
    }

    return (
        <div className="super-admin-page">
            <header className="admin-header">
                <div>
                    <h1>Tenant Management</h1>
                    <p>Manage all tenants and their access</p>
                </div>
                <div className="header-actions">
                    <button className="btn-icon" onClick={loadData} title="Refresh">
                        <RefreshCw size={18} />
                    </button>
                    <button className="btn-icon" onClick={handleLogout} title="Logout">
                        <LogOut size={18} />
                    </button>
                </div>
            </header>

            {/* Stats */}
            {stats && (
                <div className="stats-grid">
                    <div className="stat-card">
                        <Users size={20} />
                        <div>
                            <span className="stat-value">{stats.total_tenants}</span>
                            <span className="stat-label">Total Tenants</span>
                        </div>
                    </div>
                    <div className="stat-card">
                        <div className="stat-indicator active" />
                        <div>
                            <span className="stat-value">{stats.active_tenants}</span>
                            <span className="stat-label">Active</span>
                        </div>
                    </div>
                    <div className="stat-card">
                        <div className="stat-indicator inactive" />
                        <div>
                            <span className="stat-value">{stats.inactive_tenants}</span>
                            <span className="stat-label">Inactive</span>
                        </div>
                    </div>
                    <div className="stat-card">
                        <FileText size={20} />
                        <div>
                            <span className="stat-value">{stats.total_documents}</span>
                            <span className="stat-label">Documents</span>
                        </div>
                    </div>
                </div>
            )}

            {/* Tenants Table */}
            <div className="tenants-section">
                <div className="section-header">
                    <h2>Tenants ({tenants.length})</h2>
                    <button className="btn-primary" onClick={() => setShowModal(true)}>
                        <Plus size={18} />
                        Create Tenant
                    </button>
                </div>

                <div className="tenants-table">
                    <div className="table-header">
                        <span>Name</span>
                        <span>Demo ID</span>
                        <span>Documents</span>
                        <span>Status</span>
                        <span>Actions</span>
                    </div>

                    {tenants.length === 0 ? (
                        <div className="empty-state">No tenants yet. Create one to get started.</div>
                    ) : (
                        tenants.map(tenant => (
                            <div key={tenant.id} className="table-row">
                                <span className="tenant-name">{tenant.name}</span>
                                <span className="demo-id">
                                    <code>{tenant.demo_id}</code>
                                    <button
                                        className="copy-btn"
                                        onClick={() => handleCopyDemoId(tenant.demo_id)}
                                    >
                                        {copiedId === tenant.demo_id ? (
                                            <Check size={14} />
                                        ) : (
                                            <Copy size={14} />
                                        )}
                                    </button>
                                </span>
                                <span>{tenant.document_count}</span>
                                <span>
                                    <button
                                        className={`status-toggle ${tenant.is_active ? 'active' : ''}`}
                                        onClick={() => handleToggleActive(tenant)}
                                    >
                                        {tenant.is_active ? (
                                            <><ToggleRight size={18} /> Active</>
                                        ) : (
                                            <><ToggleLeft size={18} /> Inactive</>
                                        )}
                                    </button>
                                </span>
                                <span>
                                    <button
                                        className="delete-btn"
                                        onClick={() => handleDelete(tenant)}
                                    >
                                        <Trash2 size={16} />
                                    </button>
                                </span>
                            </div>
                        ))
                    )}
                </div>
            </div>

            {/* Create Modal */}
            {showModal && (
                <div className="modal-overlay" onClick={() => setShowModal(false)}>
                    <div className="modal" onClick={e => e.stopPropagation()}>
                        <h3>Create New Tenant</h3>
                        <form onSubmit={handleCreateTenant}>
                            <input
                                type="text"
                                value={newTenantName}
                                onChange={(e) => setNewTenantName(e.target.value)}
                                placeholder="Company name"
                                autoFocus
                            />
                            <div className="modal-actions">
                                <button type="button" onClick={() => setShowModal(false)}>
                                    Cancel
                                </button>
                                <button type="submit" className="btn-primary" disabled={creating || !newTenantName.trim()}>
                                    {creating ? 'Creating...' : 'Create'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default SuperAdminPage;
