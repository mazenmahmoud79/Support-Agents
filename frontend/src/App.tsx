import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from './hooks/useAuth';
import { LoginPage } from './pages/LoginPage';
import { ChatPage } from './pages/ChatPage';
import { UploadPage } from './pages/UploadPage';
import { AdminPage } from './pages/AdminPage';
import DeployPage from './pages/DeployPage';
import SuperAdminLoginPage from './pages/SuperAdminLoginPage';
import SuperAdminPage from './pages/SuperAdminPage';
import { Layout } from './components/layout/Layout';
import './styles/index.css';

function App() {
    const { isAuthenticated, initialize } = useAuthStore();

    React.useEffect(() => {
        initialize();
    }, [initialize]);

    return (
        <BrowserRouter>
            <Routes>
                {/* Super Admin Routes (outside normal auth) */}
                <Route path="/super-admin" element={<SuperAdminLoginPage />} />
                <Route path="/super-admin/dashboard" element={<SuperAdminPage />} />

                {/* Tenant Routes */}
                <Route path="/login" element={isAuthenticated ? <Navigate to="/" /> : <LoginPage />} />

                {isAuthenticated ? (
                    <Route path="/" element={<Layout />}>
                        <Route index element={<ChatPage />} />
                        <Route path="upload" element={<UploadPage />} />
                        <Route path="admin" element={<AdminPage />} />
                        <Route path="deploy" element={<DeployPage />} />
                        {/* Redirect old routes */}
                        <Route path="integration" element={<Navigate to="/deploy" />} />
                        <Route path="preview/*" element={<Navigate to="/deploy" />} />
                    </Route>
                ) : (
                    <Route path="*" element={<Navigate to="/login" />} />
                )}
            </Routes>
        </BrowserRouter>
    );
}

export default App;
