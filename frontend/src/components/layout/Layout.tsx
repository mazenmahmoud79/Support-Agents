import React from 'react';
import { Outlet, NavLink } from 'react-router-dom';
import { MessageSquare, Upload, BarChart3, LogOut, Plug } from 'lucide-react';
import { useAuthStore } from '../../hooks/useAuth';
import './Layout.css';

export const Layout: React.FC = () => {
    const { tenant, logout } = useAuthStore();

    return (
        <div className="layout">
            <nav className="sidebar">
                <div className="sidebar-header">
                    <h1>Zada</h1>
                    <span className="tenant-name">{tenant?.name}</span>
                </div>

                <div className="nav-links">
                    <NavLink to="/" className="nav-link" end>
                        <MessageSquare size={18} />
                        <span>Chat</span>
                    </NavLink>
                    <NavLink to="/upload" className="nav-link">
                        <Upload size={18} />
                        <span>Upload</span>
                    </NavLink>
                    <NavLink to="/admin" className="nav-link">
                        <BarChart3 size={18} />
                        <span>Dashboard</span>
                    </NavLink>
                    <NavLink to="/deploy" className="nav-link">
                        <Plug size={18} />
                        <span>Deploy</span>
                    </NavLink>
                </div>

                <button onClick={logout} className="logout-btn">
                    <LogOut size={18} />
                    <span>Logout</span>
                </button>
            </nav>

            <main className="main-content">
                <Outlet />
            </main>
        </div>
    );
};
