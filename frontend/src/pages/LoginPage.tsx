import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../hooks/useAuth';
import './LoginPage.css';

export const LoginPage: React.FC = () => {
    const [demoId, setDemoId] = useState('');
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    const { demoLogin } = useAuthStore();
    const navigate = useNavigate();

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setIsLoading(true);

        try {
            await demoLogin(demoId);
            navigate('/');
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Invalid demo ID');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="login-page">
            <div className="login-card">
                <h1>Zada.AI</h1>
                <p className="subtitle">Customer Service Provider</p>
                <p className="slogan">Create Your AI Support Agent</p>

                {error && <div className="error-message">{error}</div>}

                <form onSubmit={handleLogin} className="login-form">
                    <div className="form-group">
                        <label htmlFor="demoId">Access Key</label>
                        <input
                            id="demoId"
                            type="text"
                            value={demoId}
                            onChange={(e) => setDemoId(e.target.value.toUpperCase())}
                            placeholder="Enter access key..."
                            required
                            disabled={isLoading}
                            maxLength={11}
                            style={{ textTransform: 'uppercase', letterSpacing: '1px' }}
                        />
                    </div>

                    <button
                        type="submit"
                        className="btn btn-primary submit-btn"
                        disabled={isLoading || !demoId}
                    >
                        {isLoading ? (
                            <>
                                <div className="spinner" />
                                Connecting...
                            </>
                        ) : (
                            'Login'
                        )}
                    </button>
                </form>
            </div>
        </div>
    );
};
