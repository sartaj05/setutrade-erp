import { useMemo, useState } from 'react';
import Brand from '../components/Brand';
import Icon from '../components/Icon';
import { demoAccounts } from '../data/demoData';
import { useAuth } from '../context/AuthContext';
import { confirmPasswordReset, requestPasswordReset } from '../services/api';

export default function LoginPage({ navigate }) {
  const { login } = useAuth();
  const appMode = String(import.meta.env.VITE_APP_MODE || 'demo').toLowerCase();
  const demoMode = appMode === 'demo';
  const query = useMemo(() => new URLSearchParams(window.location.search), []);
  const resetUid = query.get('reset_uid');
  const resetToken = query.get('reset_token');
  const [view, setView] = useState(resetUid && resetToken ? 'reset' : 'login');
  const [email, setEmail] = useState(demoMode ? 'owner@setustock.demo' : '');
  const [password, setPassword] = useState(demoMode ? 'demo123' : '');
  const [newPassword, setNewPassword] = useState('');
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);

  const submit = async (e) => {
    e.preventDefault(); setError(''); setMessage(''); setLoading(true);
    try { await login(email, password); navigate('/app'); }
    catch (err) { setError(err.message); }
    finally { setLoading(false); }
  };

  const forgot = async (e) => {
    e.preventDefault(); setError(''); setMessage(''); setLoading(true);
    try {
      const result = await requestPasswordReset(email);
      setMessage(result.detail || 'If the account exists, reset instructions were sent.');
      if (result.demoReset?.url) setMessage(`${result.detail} Demo reset URL: ${result.demoReset.url}`);
    } catch (err) { setError(err.message); }
    finally { setLoading(false); }
  };

  const reset = async (e) => {
    e.preventDefault(); setError(''); setMessage(''); setLoading(true);
    try {
      await confirmPasswordReset(resetUid, resetToken, newPassword);
      window.history.replaceState({}, '', '/login');
      setView('login'); setNewPassword(''); setMessage('Password updated. Sign in with your new password.');
    } catch (err) { setError(err.message); }
    finally { setLoading(false); }
  };

  const useAccount = (account) => { setEmail(account.email); setPassword('demo123'); setError(''); };

  return (
    <div className="login-page">
      <aside className="login-story">
        <button className="back-link" onClick={() => navigate('/')}>← Back to home</button>
        <div className="login-story-inner">
          <Brand />
          <div className="story-copy">
            <span className="story-tag">B2B operations, made calmer</span>
            <h1>One place to know what is selling, what is stuck and what is still unpaid.</h1>
            <p>A role-aware workspace for wholesale teams that need clear stock, order and credit visibility without enterprise-software theatre.</p>
          </div>
          <div className="story-proof"><div><strong>34</strong><span>open orders</span></div><div><strong>8</strong><span>low-stock SKUs</span></div><div><strong>₹4.72L</strong><span>receivable</span></div></div>
        </div>
      </aside>

      <main className="login-panel">
        <div className="login-box">
          <div className="login-heading">
            <span className="demo-pill"><span /> {demoMode ? 'Safe demo workspace' : 'Production workspace'}</span>
            <h2>{view === 'login' ? 'Welcome back' : view === 'forgot' ? 'Reset your password' : 'Choose a new password'}</h2>
            <p>{demoMode ? 'Demo accounts use browser-safe sample data when the Django API is unavailable.' : 'This deployment requires the live Django API. Real business data never falls back to demo records.'}</p>
          </div>

          {view === 'login' && <form onSubmit={submit} className="login-form">
            <label>Email address<input type="email" value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="email" required /></label>
            <label>Password<input type="password" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="current-password" required /></label>
            {error && <div className="form-error">{error}</div>}{message && <div className="form-success">{message}</div>}
            <button className="btn btn-primary login-submit" disabled={loading}>{loading ? 'Signing in…' : <>Sign in <Icon name="arrow" size={17} /></>}</button>
            {!demoMode && <button type="button" className="link-button" onClick={() => { setView('forgot'); setError(''); setMessage(''); }}>Forgot password?</button>}
          </form>}

          {view === 'forgot' && <form onSubmit={forgot} className="login-form">
            <label>Email address<input type="email" value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="email" required /></label>
            {error && <div className="form-error">{error}</div>}{message && <div className="form-success">{message}</div>}
            <button className="btn btn-primary login-submit" disabled={loading}>{loading ? 'Sending…' : 'Send reset instructions'}</button>
            <button type="button" className="link-button" onClick={() => setView('login')}>Back to sign in</button>
          </form>}

          {view === 'reset' && <form onSubmit={reset} className="login-form">
            <label>New password<input type="password" minLength="8" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} autoComplete="new-password" required /></label>
            {error && <div className="form-error">{error}</div>}
            <button className="btn btn-primary login-submit" disabled={loading}>{loading ? 'Updating…' : 'Update password'}</button>
          </form>}

          {view === 'login' && demoMode && <div className="demo-selector">
            <div className="selector-head"><span>Quick role switch</span><small>Password: demo123</small></div>
            <div className="demo-account-grid">{demoAccounts.map((account) => <button type="button" className={email === account.email ? 'demo-account active' : 'demo-account'} key={account.role} onClick={() => useAccount(account)}><span className="role-avatar">{account.role[0]}</span><span><strong>{account.role.charAt(0) + account.role.slice(1).toLowerCase()}</strong><small>{account.name}</small></span></button>)}</div>
          </div>}
          <p className="login-footnote">{demoMode ? 'Demo data is sample-only. Do not use it for real accounting or GST filing.' : 'Your access is company-scoped and role-controlled.'}</p>
        </div>
      </main>
    </div>
  );
}
