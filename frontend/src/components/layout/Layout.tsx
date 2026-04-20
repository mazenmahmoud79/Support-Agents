import React from 'react';
import { Outlet, NavLink } from 'react-router-dom';
import { MessageSquare, Upload, BarChart3, LogOut, Plug, Headphones } from 'lucide-react';
import { useAuthStore } from '../../hooks/useAuth';
import './Layout.css';

export const Layout: React.FC = () => {
    const { tenant, user, logout } = useAuthStore();

    const initials = (tenant?.name || user?.email || 'Z')
        .split(' ').map((w: string) => w[0]).join('').slice(0, 2).toUpperCase();

    return (
        <div className="layout">
            <nav className="sidebar">
                <div className="sidebar-header">
                    <div className="sidebar-logo">Zada<span>.ai</span></div>
                    <span className="tenant-name">{tenant?.name}</span>
                </div>

                <div className="nav-links">
                    <NavLink to="/" className="nav-link" end>
                        <MessageSquare size={17} />
                        <span>Chat</span>
                    </NavLink>
                    <NavLink to="/agent-assist" className="nav-link">
                        <Headphones size={17} />
                        <span>Agent Assist</span>
                    </NavLink>
                    <NavLink to="/upload" className="nav-link">
                        <Upload size={17} />
                        <span>Knowledge Base</span>
                    </NavLink>
                    <NavLink to="/admin" className="nav-link">
                        <BarChart3 size={17} />
                        <span>Dashboard</span>
                    </NavLink>
                    <NavLink to="/deploy" className="nav-link">
                        <Plug size={17} />
                        <span>Deploy</span>
                    </NavLink>
                </div>

                <div className="sidebar-footer">
                    <div className="sidebar-user">
                        <div className="user-avatar">{initials}</div>
                        <div className="user-info">
                            <div className="user-org">{tenant?.name || 'My Workspace'}</div>
                        </div>
                    </div>
                    <button onClick={logout} className="logout-btn">
                        <LogOut size={15} />
                        <span>Log out</span>
                    </button>
                </div>
            </nav>

            <main className="main-content">
                <Outlet />
            </main>
        </div>
    );
};
