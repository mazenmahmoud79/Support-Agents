import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { GoogleOAuthProvider } from '@react-oauth/google';
import { useAuthStore } from './hooks/useAuth';
import { LoginPage } from './pages/LoginPage';
import SignupPage from './pages/SignupPage';
import VerifyEmailPage from './pages/VerifyEmailPage';
import { ChatPage } from './pages/ChatPage';
import { UploadPage } from './pages/UploadPage';
import { AdminPage } from './pages/AdminPage';
import DeployPage from './pages/DeployPage';
import AgentAssistPage from './pages/AgentAssistPage';
import SuperAdminLoginPage from './pages/SuperAdminLoginPage';
import SuperAdminPage from './pages/SuperAdminPage';
import { Layout } from './components/layout/Layout';
import './styles/index.css';

const GOOGLE_CLIENT_ID = (import.meta as any).env?.VITE_GOOGLE_CLIENT_ID || '';

function App() {
    const { isAuthenticated, isVerified, initialize } = useAuthStore();

    React.useEffect(() => {
        initialize();
    }, [initialize]);

    return (
        <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
            <BrowserRouter>
                <Routes>
                    {/* Super Admin Routes (outside normal auth) */}
                    <Route path="/super-admin" element={<SuperAdminLoginPage />} />
                    <Route path="/super-admin/dashboard" element={<SuperAdminPage />} />

                    {/* Public auth routes */}
                    <Route path="/login" element={isAuthenticated && isVerified ? <Navigate to="/" /> : <LoginPage />} />
                    <Route path="/signup" element={isAuthenticated && isVerified ? <Navigate to="/" /> : <SignupPage />} />
                    <Route path="/verify-email" element={<VerifyEmailPage />} />

                    {/* Protected routes — must be authenticated AND verified */}
                    {isAuthenticated && isVerified ? (
                        <Route path="/" element={<Layout />}>
                            <Route index element={<ChatPage />} />
                            <Route path="upload" element={<UploadPage />} />
                            <Route path="admin" element={<AdminPage />} />
                            <Route path="deploy" element={<DeployPage />} />
                            <Route path="agent-assist" element={<AgentAssistPage />} />
                            <Route path="integration" element={<Navigate to="/deploy" />} />
                            <Route path="preview/*" element={<Navigate to="/deploy" />} />
                        </Route>
                    ) : (
                        <Route path="*" element={<Navigate to="/login" />} />
                    )}
                </Routes>
            </BrowserRouter>
        </GoogleOAuthProvider>
    );
}

export default App;
