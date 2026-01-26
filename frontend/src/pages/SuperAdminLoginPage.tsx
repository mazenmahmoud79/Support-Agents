import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Lock, AlertCircle } from 'lucide-react';
import { superAdminService } from '../services/superAdminService';
import './SuperAdminLoginPage.css';

const SuperAdminLoginPage: React.FC = () => {
    const navigate = useNavigate();
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            const success = await superAdminService.login(password);
            if (success) {
                navigate('/super-admin/dashboard');
            } else {
                setError('Invalid password');
            }
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Login failed');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="super-admin-login">
            <div className="login-card">
                <div className="login-header">
                    <div className="lock-icon">
                        <Lock size={24} />
                    </div>
                    <h1>Admin Access</h1>
                    <p>Enter your admin password</p>
                </div>

                <form onSubmit={handleSubmit}>
                    {error && (
                        <div className="error-message">
                            <AlertCircle size={16} />
                            {error}
                        </div>
                    )}

                    <div className="input-group">
                        <input
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            placeholder="Password"
                            autoFocus
                            disabled={loading}
                        />
                    </div>

                    <button type="submit" disabled={loading || !password}>
                        {loading ? 'Verifying...' : 'Continue'}
                    </button>
                </form>
            </div>
        </div>
    );
};

export default SuperAdminLoginPage;
