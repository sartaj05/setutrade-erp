import { createContext, useContext, useEffect, useMemo, useState } from 'react';
import { demoAccounts, permissions } from '../data/demoData';
import { getApiResource, loginApi, logoutApi, registerApi } from '../services/api';

const AuthContext = createContext(null);
const STORAGE_KEY = 'setustock_auth';
const REGISTERED_DEMO_KEY = 'setustock_registered_demo_accounts';
const DEMO_PASSWORD_KEY = 'setustock_demo_password_overrides';

function readStoredUser() {
  try { return JSON.parse(localStorage.getItem(STORAGE_KEY)) || null; }
  catch { return null; }
}

function readRegisteredDemoAccounts() {
  try { return JSON.parse(localStorage.getItem(REGISTERED_DEMO_KEY)) || []; }
  catch { return []; }
}

function readDemoPasswordOverrides() {
  try { return JSON.parse(localStorage.getItem(DEMO_PASSWORD_KEY)) || {}; }
  catch { return {}; }
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(readStoredUser);
  const [mode, setMode] = useState(user?.mode || 'demo');
  const [sessionReady, setSessionReady] = useState(false);

  useEffect(() => {
    let cancelled = false;
    const stored = readStoredUser();

    const finish = (nextUser, nextMode = nextUser?.mode || 'demo') => {
      if (cancelled) return;
      setUser(nextUser);
      setMode(nextMode);
      setSessionReady(true);
    };

    if (!stored) {
      finish(null, 'demo');
      return () => { cancelled = true; };
    }

    if (stored.mode !== 'api') {
      finish(stored, 'demo');
      return () => { cancelled = true; };
    }

    const token = localStorage.getItem('setustock_token');
    if (!token) {
      localStorage.removeItem(STORAGE_KEY);
      finish(null, 'demo');
      return () => { cancelled = true; };
    }

    getApiResource('auth/me').then((payload) => {
      const nextUser = { ...payload.user, mode: 'api' };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(nextUser));
      finish(nextUser, 'api');
    }).catch((error) => {
      // Keep a cached session during a temporary network outage, but remove
      // it when Django explicitly says that the session is no longer valid.
      if (error.status === 401 || error.status === 403) {
        localStorage.removeItem(STORAGE_KEY);
        localStorage.removeItem('setustock_token');
        localStorage.removeItem('setustock_refresh_token');
        finish(null, 'demo');
      } else {
        finish(stored, 'api');
      }
    });

    return () => { cancelled = true; };
  }, []);

  const loginDemo = async (email, password) => {
    const demoEnabled = String(import.meta.env.VITE_APP_MODE || 'demo').toLowerCase() === 'demo';
    if (!demoEnabled) throw new Error('Demo login is disabled on this deployment.');
    await new Promise((resolve) => setTimeout(resolve, 120));
    const overrides = readDemoPasswordOverrides();
    const account = [...demoAccounts, ...readRegisteredDemoAccounts()].find((item) => item.email.toLowerCase() === email.trim().toLowerCase() && (overrides[item.email.toLowerCase()] || item.password) === password);
    if (!account) throw new Error('Invalid email or password. Use one of the demo accounts shown below.');
    const safeUser = { id: account.id, name: account.name, email: account.email, role: account.role, business: account.business, permissions: permissions[account.role] || ['dashboard'], mode: 'demo' };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(safeUser));
    setUser(safeUser); setMode('demo');
    return safeUser;
  };

  const registerDemo = async ({ name, email, password, businessName, phone }) => {
    const demoEnabled = String(import.meta.env.VITE_APP_MODE || 'demo').toLowerCase() === 'demo';
    if (!demoEnabled) throw new Error('Demo registration is disabled on this deployment.');
    if (password.length < 8) throw new Error('Password must be at least 8 characters.');
    const accounts = readRegisteredDemoAccounts();
    if ([...demoAccounts, ...accounts].some((item) => item.email.toLowerCase() === email.trim().toLowerCase())) throw new Error('An account with this email already exists.');
    const account = { id: `demo-${Date.now()}`, name: name.trim(), email: email.trim().toLowerCase(), password, role: 'OWNER', business: businessName.trim() || `${name.trim()} Distributors`, phone: phone.trim() };
    localStorage.setItem(REGISTERED_DEMO_KEY, JSON.stringify([...accounts, account]));
    const safeUser = { id: account.id, name: account.name, email: account.email, role: account.role, business: account.business, permissions: permissions[account.role] || ['dashboard'], mode: 'demo' };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(safeUser));
    setUser(safeUser); setMode('demo');
    return safeUser;
  };

  const resetDemoPassword = async (email, newPassword) => {
    if (newPassword.length < 8) throw new Error('Password must be at least 8 characters.');
    const exists = [...demoAccounts, ...readRegisteredDemoAccounts()].some((item) => item.email.toLowerCase() === email.trim().toLowerCase());
    if (!exists) throw new Error('No demo account was found for this email.');
    const overrides = readDemoPasswordOverrides();
    overrides[email.trim().toLowerCase()] = newPassword;
    localStorage.setItem(DEMO_PASSWORD_KEY, JSON.stringify(overrides));
  };

  const login = async (email, password) => {
    const demoMode = String(import.meta.env.VITE_APP_MODE || 'demo').toLowerCase() === 'demo';
    const fallbackEnabled = demoMode && String(import.meta.env.VITE_DEMO_FALLBACK ?? 'true').toLowerCase() !== 'false';
    try {
      const apiUser = await loginApi(email, password);
      const safeUser = { ...apiUser, mode: 'api' };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(safeUser));
      setUser(safeUser); setMode('api');
      return safeUser;
    } catch (error) {
      if (!error.network || !fallbackEnabled) throw error;
      return loginDemo(email, password);
    }
  };

  const register = async (details) => {
    const demoMode = String(import.meta.env.VITE_APP_MODE || 'demo').toLowerCase() === 'demo';
    const fallbackEnabled = demoMode && String(import.meta.env.VITE_DEMO_FALLBACK ?? 'true').toLowerCase() !== 'false';
    try {
      const apiUser = await registerApi(details);
      const safeUser = { ...apiUser, mode: 'api' };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(safeUser));
      setUser(safeUser); setMode('api');
      return safeUser;
    } catch (error) {
      if (!error.network || !fallbackEnabled) throw error;
      return registerDemo(details);
    }
  };

  const logout = async () => {
    if (mode === 'api') await logoutApi();
    localStorage.removeItem(STORAGE_KEY);
    localStorage.removeItem('setustock_token');
    localStorage.removeItem('setustock_refresh_token');
    setUser(null); setMode('demo');
  };

  const can = (module) => Boolean(user && (user.permissions || permissions[user.role] || []).includes(module));
  const value = useMemo(() => ({ user, mode, sessionReady, login, register, loginDemo, registerDemo, resetDemoPassword, logout, can, setUser }), [user, mode, sessionReady]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider');
  return ctx;
}
