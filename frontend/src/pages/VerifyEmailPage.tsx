import React, { useEffect, useState } from 'react';
import { useNavigate, useLocation, useSearchParams, Link } from 'react-router-dom';
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

    // Auto-verify when token is in URL
    useEffect(() => {
        if (token) {
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
        }
    }, [token]);

    // Resend verification with cooldown
    const handleResend = async () => {
        if (!resendEmail) return;
        try {
            await authService.resendVerification(resendEmail);
            setResendCooldown(60);
            const interval = setInterval(() => {
                setResendCooldown((c) => {
                    if (c <= 1) { clearInterval(interval); return 0; }
                    return c - 1;
                });
            }, 1000);
        } catch {
            // Silently ignore — backend always returns 200
        }
    };

    if (status === 'verifying') {
        return (
            <div className="login-page">
                <div className="login-card">
                    <div className="verify-pending">
                        <div className="icon">⏳</div>
                        <h2>Verifying your email...</h2>
                    </div>
                </div>
            </div>
        );
    }

    if (status === 'success') {
        return (
            <div className="login-page">
                <div className="login-card">
                    <div className="verify-pending">
                        <div className="icon">✅</div>
                        <h2>Email verified!</h2>
                        <p>Redirecting you to your dashboard…</p>
                    </div>
                </div>
            </div>
        );
    }

    if (status === 'error') {
        return (
            <div className="login-page">
                <div className="login-card">
                    <h1>Zada.AI</h1>
                    <div className="verify-pending">
                        <div className="icon">❌</div>
                        <h2>Verification failed</h2>
                        <p>{message}</p>
                    </div>
                    <div className="form-group" style={{ marginTop: '1rem' }}>
                        <label htmlFor="resendEmail">Request a new link</label>
                        <input
                            id="resendEmail"
                            type="email"
                            value={resendEmail}
                            onChange={(e) => setResendEmail(e.target.value)}
                            placeholder="your@email.com"
                        />
                    </div>
                    <button
                        className="resend-btn"
                        onClick={handleResend}
                        disabled={resendCooldown > 0 || !resendEmail}
                        style={{ marginTop: '0.75rem', width: '100%' }}
                    >
                        {resendCooldown > 0 ? `Resend in ${resendCooldown}s` : 'Resend verification email'}
                    </button>
                    <p className="auth-footer-link" style={{ marginTop: '1rem' }}>
                        <Link to="/login">Back to login</Link>
                    </p>
                </div>
            </div>
        );
    }

    // status === 'pending' — user just registered, waiting to verify
    return (
        <div className="login-page">
            <div className="login-card">
                <h1>Zada.AI</h1>
                <div className="verify-pending">
                    <div className="icon">📬</div>
                    <h2>Check your email</h2>
                    <p>
                        We sent a verification link to <strong>{email || 'your email address'}</strong>.
                        Click the link to activate your account.
                    </p>
                    <p style={{ fontSize: '0.85rem', marginBottom: '1.5rem' }}>
                        Didn't receive it? Check your spam folder or request a new link below.
                    </p>
                </div>

                <button
                    className="resend-btn"
                    onClick={handleResend}
                    disabled={resendCooldown > 0 || !resendEmail}
                    style={{ width: '100%', marginBottom: '1rem' }}
                >
                    {resendCooldown > 0 ? `Resend in ${resendCooldown}s` : 'Resend verification email'}
                </button>

                <p className="auth-footer-link">
                    <Link to="/login">Back to login</Link>
                </p>
            </div>
        </div>
    );
};

export default VerifyEmailPage;
