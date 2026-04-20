import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { GoogleLogin } from '@react-oauth/google';
import { Bot, Zap, ShieldCheck } from 'lucide-react';
import { useAuthStore } from '../hooks/useAuth';
import './LoginPage.css';

const SignupPage: React.FC = () => {
    const [orgName, setOrgName] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    const { register, googleLogin } = useAuthStore();
    const navigate = useNavigate();

    const handleSignup = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        if (password !== confirmPassword) { setError('Passwords do not match'); return; }
        if (password.length < 8) { setError('Password must be at least 8 characters'); return; }
        setIsLoading(true);
        try {
            await register(email, password, orgName);
            navigate('/verify-email', { state: { email } });
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Registration failed. Please try again.');
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
            setError(err.response?.data?.detail || 'Google signup failed');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="auth-page">
            <div className="auth-brand">
                <div className="brand-logo">Zada<span>.ai</span></div>
                <p className="brand-tagline">
                    Set up your AI support agent<br />in minutes, not weeks.
                </p>
                <div className="brand-features">
                    <div className="brand-feature">
                        <div className="brand-feature-icon"><Bot size={16} /></div>
                        <div className="brand-feature-text">
                            <strong>No code needed</strong>
                            <span>Upload docs and go live instantly</span>
                        </div>
                    </div>
                    <div className="brand-feature">
                        <div className="brand-feature-icon"><Zap size={16} /></div>
                        <div className="brand-feature-text">
                            <strong>Embed anywhere</strong>
                            <span>One snippet, any website</span>
                        </div>
                    </div>
                    <div className="brand-feature">
                        <div className="brand-feature-icon"><ShieldCheck size={16} /></div>
                        <div className="brand-feature-text">
                            <strong>Free to start</strong>
                            <span>No credit card required</span>
                        </div>
                    </div>
                </div>
            </div>

            <div className="auth-form-panel">
                <div className="auth-form-inner">
                    <h2>Create your account</h2>
                    <p className="auth-subtitle">Start your free workspace today</p>

                    {error && <div className="error-message" style={{ marginBottom: '1.25rem' }}>{error}</div>}

                    <form onSubmit={handleSignup} className="login-form">
                        <div className="form-group">
                            <label htmlFor="orgName">Organization Name</label>
                            <input
                                id="orgName"
                                type="text"
                                value={orgName}
                                onChange={(e) => setOrgName(e.target.value)}
                                placeholder="Acme Corp"
                                required
                                disabled={isLoading}
                                maxLength={255}
                            />
                        </div>
                        <div className="form-group">
                            <label htmlFor="email">Work Email</label>
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
                                placeholder="Min. 8 characters"
                                required
                                disabled={isLoading}
                                minLength={8}
                            />
                        </div>
                        <div className="form-group">
                            <label htmlFor="confirmPassword">Confirm Password</label>
                            <input
                                id="confirmPassword"
                                type="password"
                                value={confirmPassword}
                                onChange={(e) => setConfirmPassword(e.target.value)}
                                placeholder="Repeat password"
                                required
                                disabled={isLoading}
                            />
                        </div>
                        <button
                            type="submit"
                            className="btn btn-primary submit-btn"
                            disabled={isLoading || !orgName || !email || !password || !confirmPassword}
                        >
                            {isLoading ? <><div className="spinner" />Creating account…</> : 'Create Account'}
                        </button>
                    </form>

                    <div className="auth-divider"><span>or</span></div>

                    <div className="google-btn-wrapper">
                        <GoogleLogin
                            onSuccess={handleGoogleSuccess}
                            onError={() => setError('Google signup failed')}
                            width="360"
                            text="signup_with"
                        />
                    </div>

                    <p className="auth-footer-link">
                        Already have an account? <Link to="/login">Sign in</Link>
                    </p>
                </div>
            </div>
        </div>
    );
};

export default SignupPage;
