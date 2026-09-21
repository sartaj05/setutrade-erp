import { useState } from 'react';
import Brand from '../components/Brand';
import Icon from '../components/Icon';
import { demoAccounts } from '../data/demoData';
import { useAuth } from '../context/AuthContext';

export default function LoginPage({ navigate }) {
  const { loginDemo } = useAuth();
  const [email, setEmail] = useState('owner@setustock.demo');
  const [password, setPassword] = useState('demo123');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await loginDemo(email, password);
      navigate('/app');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const useAccount = (account) => {
    setEmail(account.email);
    setPassword('demo123');
    setError('');
  };

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
          <div className="story-proof">
            <div><strong>34</strong><span>open orders</span></div>
            <div><strong>8</strong><span>low-stock SKUs</span></div>
            <div><strong>₹4.72L</strong><span>receivable</span></div>
          </div>
        </div>
      </aside>

      <main className="login-panel">
        <div className="login-box">
          <div className="login-heading">
            <span className="demo-pill"><span /> Demo workspace</span>
            <h2>Welcome back</h2>
            <p>Use a demo role below. The same screen later connects to Django authentication.</p>
          </div>

          <form onSubmit={submit} className="login-form">
            <label>Email address<input type="email" value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="email" required /></label>
            <label>Password<input type="password" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="current-password" required /></label>
            {error && <div className="form-error">{error}</div>}
            <button className="btn btn-primary login-submit" disabled={loading}>{loading ? 'Signing in…' : <>Sign in <Icon name="arrow" size={17} /></>}</button>
          </form>

          <div className="demo-selector">
            <div className="selector-head"><span>Quick role switch</span><small>Password: demo123</small></div>
            <div className="demo-account-grid">
              {demoAccounts.map((account) => (
                <button type="button" className={email === account.email ? 'demo-account active' : 'demo-account'} key={account.role} onClick={() => useAccount(account)}>
                  <span className="role-avatar">{account.role[0]}</span>
                  <span><strong>{account.role.charAt(0) + account.role.slice(1).toLowerCase()}</strong><small>{account.name}</small></span>
                </button>
              ))}
            </div>
          </div>
          <p className="login-footnote">Demo data is stored in your browser only. No real customer or financial data is used.</p>
        </div>
      </main>
    </div>
  );
}
