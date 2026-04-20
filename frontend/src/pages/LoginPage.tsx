import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { GoogleLogin } from '@react-oauth/google';
import { Bot, Zap, ShieldCheck } from 'lucide-react';
import { useAuthStore } from '../hooks/useAuth';
import './LoginPage.css';

export const LoginPage: React.FC = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    const { emailLogin, googleLogin } = useAuthStore();
    const navigate = useNavigate();

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setIsLoading(true);
        try {
            await emailLogin(email, password);
            navigate('/');
        } catch (err: any) {
            if (err.response?.status === 403) {
                navigate('/verify-email', { state: { email } });
            } else {
                setError(err.response?.data?.detail || 'Invalid email or password');
            }
        } finally {
            setIsLoading(false);
        }
    };

    const handleGoogleSuccess = async (credentialResponse: any) => {
        setError('');
        setIsLoading(true);
        try {
            await googleLogin(credentialResponse.credential);
            navigate('/');
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Google login failed');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="auth-page">
            {/* Left brand panel */}
            <div className="auth-brand">
                <div className="brand-logo">Zada<span>.ai</span></div>
                <p className="brand-tagline">
                    AI-powered customer support,<br />built for your team.
                </p>
                <div className="brand-features">
                    <div className="brand-feature">
                        <div className="brand-feature-icon"><Bot size={16} /></div>
                        <div className="brand-feature-text">
                            <strong>Instant AI Answers</strong>
                            <span>Trained on your knowledge base</span>
                        </div>
                    </div>
                    <div className="brand-feature">
                        <div className="brand-feature-icon"><Zap size={16} /></div>
                        <div className="brand-feature-text">
                            <strong>Multi-channel Deploy</strong>
                            <span>Web, WhatsApp & more</span>
                        </div>
                    </div>
                    <div className="brand-feature">
                        <div className="brand-feature-icon"><ShieldCheck size={16} /></div>
                        <div className="brand-feature-text">
                            <strong>Secure & Private</strong>
                            <span>Your data stays yours</span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Right form panel */}
            <div className="auth-form-panel">
                <div className="auth-form-inner">
                    <h2>Welcome back</h2>
                    <p className="auth-subtitle">Sign in to your workspace</p>

                    {error && <div className="error-message" style={{ marginBottom: '1.25rem' }}>{error}</div>}

                    <form onSubmit={handleLogin} className="login-form">
                        <div className="form-group">
                            <label htmlFor="email">Email</label>
                            <input
                                id="email"
                                type="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                placeholder="you@company.com"
                                required
                                disabled={isLoading}
                            />
                        </div>
                        <div className="form-group">
                            <label htmlFor="password">Password</label>
                            <input
                                id="password"
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                placeholder="••••••••"
                                required
                                disabled={isLoading}
                            />
                        </div>
                        <button
                            type="submit"
                            className="btn btn-primary submit-btn"
                            disabled={isLoading || !email || !password}
                        >
                            {isLoading ? <><div className="spinner" />Signing in…</> : 'Sign In'}
                        </button>
                    </form>

                    <div className="auth-divider"><span>or</span></div>

                    <div className="google-btn-wrapper">
                        <GoogleLogin
                            onSuccess={handleGoogleSuccess}
                            onError={() => setError('Google login failed')}
                            width="360"
                            text="signin_with"
                        />
                    </div>

                    <p className="auth-footer-link">
                        Don't have an account? <Link to="/signup">Create one free</Link>
                    </p>
                </div>
            </div>
        </div>
    );
};
