import React, { useEffect, useState } from 'react';
import { useNavigate, useLocation, useSearchParams, Link } from 'react-router-dom';
import { Mail, CheckCircle, XCircle } from 'lucide-react';
import { useAuthStore } from '../hooks/useAuth';
import { authService } from '../services/authService';
import './LoginPage.css';

const VerifyEmailPage: React.FC = () => {
    const [searchParams] = useSearchParams();
    const location = useLocation();
    const navigate = useNavigate();

    const token = searchParams.get('token');
    const email = (location.state as any)?.email || '';

    const [status, setStatus] = useState<'pending' | 'verifying' | 'success' | 'error'>('pending');
    const [message, setMessage] = useState('');
    const [resendCooldown, setResendCooldown] = useState(0);
    const [resendEmail, setResendEmail] = useState(email);

    useEffect(() => {
        if (!token) return;
        setStatus('verifying');
        authService.verifyEmail(token)
            .then(({ access_token }) => {
                localStorage.setItem('token', access_token);
                return authService.getCurrentUser();
            })
            .then((user) => {
                useAuthStore.setState({
                    isAuthenticated: true,
                    isVerified: true,
                    user,
                    tenant: user.tenant,
                    token: localStorage.getItem('token'),
                });
                setStatus('success');
                setTimeout(() => navigate('/'), 1500);
            })
            .catch((err) => {
                setStatus('error');
                setMessage(err.response?.data?.detail || 'Verification failed. The link may be expired.');
            });
    }, [token]);

    const handleResend = async () => {
        if (!resendEmail) return;
        try {
            await authService.resendVerification(resendEmail);
            setResendCooldown(60);
            const interval = setInterval(() => {
                setResendCooldown((c) => { if (c <= 1) { clearInterval(interval); return 0; } return c - 1; });
            }, 1000);
        } catch { /* backend always 200 */ }
    };

    if (status === 'verifying') return (
        <div className="auth-page">
            <div className="auth-brand">
                <div className="brand-logo">Zada<span>.ai</span></div>
            </div>
            <div className="auth-form-panel">
                <div className="auth-form-inner">
                    <div className="verify-pending">
                        <div className="verify-icon">
                            <div className="spinner spinner-dark" style={{ width: 28, height: 28 }} />
                        </div>
                        <h2>Verifying your email…</h2>
                        <p>Just a moment</p>
                    </div>
                </div>
            </div>
        </div>
    );

    if (status === 'success') return (
        <div className="auth-page">
            <div className="auth-brand">
                <div className="brand-logo">Zada<span>.ai</span></div>
            </div>
            <div className="auth-form-panel">
                <div className="auth-form-inner">
                    <div className="verify-pending">
                        <div className="verify-icon" style={{ background: 'var(--success-bg)', color: 'var(--success)' }}>
                            <CheckCircle size={32} />
                        </div>
                        <h2>Email verified!</h2>
                        <p>Redirecting you to your dashboard…</p>
                    </div>
                </div>
            </div>
        </div>
    );

    if (status === 'error') return (
        <div className="auth-page">
            <div className="auth-brand">
                <div className="brand-logo">Zada<span>.ai</span></div>
            </div>
            <div className="auth-form-panel">
                <div className="auth-form-inner">
                    <div className="verify-pending" style={{ marginBottom: '1.5rem' }}>
                        <div className="verify-icon" style={{ background: 'var(--danger-bg)', color: 'var(--danger)' }}>
                            <XCircle size={32} />
                        </div>
                        <h2>Verification failed</h2>
                        <p>{message}</p>
                    </div>
                    <div className="form-group" style={{ marginBottom: '0.75rem' }}>
                        <label htmlFor="resendEmail">Resend to</label>
                        <input
                            id="resendEmail"
                            type="email"
                            value={resendEmail}
                            onChange={(e) => setResendEmail(e.target.value)}
                            placeholder="your@email.com"
                        />
                    </div>
                    <button className="resend-btn" onClick={handleResend} disabled={resendCooldown > 0 || !resendEmail}>
                        {resendCooldown > 0 ? `Resend in ${resendCooldown}s` : 'Resend verification email'}
                    </button>
                    <p className="auth-footer-link" style={{ marginTop: '1.25rem' }}>
                        <Link to="/login">Back to login</Link>
                    </p>
                </div>
            </div>
        </div>
    );

    return (
        <div className="auth-page">
            <div className="auth-brand">
                <div className="brand-logo">Zada<span>.ai</span></div>
                <p className="brand-tagline">One more step to get started</p>
            </div>
            <div className="auth-form-panel">
                <div className="auth-form-inner">
                    <div className="verify-pending" style={{ marginBottom: '1.5rem' }}>
                        <div className="verify-icon">
                            <Mail size={30} />
                        </div>
                        <h2>Check your inbox</h2>
                        <p>
                            We sent a verification link to{' '}
                            <strong>{email || 'your email address'}</strong>.
                            Click the link to activate your account.
                        </p>
                        <p style={{ fontSize: '0.8rem', color: 'var(--text-subtle)', marginBottom: 0 }}>
                            Didn't get it? Check spam or resend below.
                        </p>
                    </div>
                    <button
                        className="resend-btn"
                        onClick={handleResend}
                        disabled={resendCooldown > 0 || !resendEmail}
                        style={{ marginBottom: '1rem' }}
                    >
                        {resendCooldown > 0 ? `Resend in ${resendCooldown}s` : 'Resend verification email'}
                    </button>
                    <p className="auth-footer-link">
                        <Link to="/login">Back to login</Link>
                    </p>
                </div>
            </div>
        </div>
    );
};

export default VerifyEmailPage;
