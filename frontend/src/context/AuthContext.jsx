import { createContext, useContext, useEffect, useMemo, useState } from 'react';
import { demoAccounts, permissions } from '../data/demoData';
import { clearAuthTokens, getAccessToken, getApiResource, loginApi, logoutApi, registerApi } from '../services/api';
import { planAllows } from '../data/plans';

const AuthContext = createContext(null);
const STORAGE_KEY = 'setustock_auth';
const SESSION_STORAGE_KEY = 'setustock_auth_session';
const PERSISTENT_STORAGE_KEY = 'setustock_auth_persistent';
const REGISTERED_DEMO_KEY = 'setustock_registered_demo_accounts';
const DEMO_PASSWORD_KEY = 'setustock_demo_password_overrides';
const PERSISTENT_SESSION_MAX_AGE = 14 * 24 * 60 * 60 * 1000;

function readJson(storage, key) {
  try { return JSON.parse(storage.getItem(key)) || null; }
  catch { return null; }
}

function removeKey(storage, key) {
  try { storage.removeItem(key); } catch { /* storage may be unavailable */ }
}

function readStoredAuth() {
  const session = readJson(sessionStorage, SESSION_STORAGE_KEY);
  if (session?.user) return { user: session.user, remember: false };

  const persistent = readJson(localStorage, PERSISTENT_STORAGE_KEY);
  if (persistent?.user && (!persistent.expiresAt || persistent.expiresAt > Date.now())) {
    return { user: persistent.user, remember: true };
  }
  if (persistent) {
    removeKey(localStorage, PERSISTENT_STORAGE_KEY);
    clearAuthTokens();
  }

  // Clear the old unscoped localStorage session once. It caused demo users
  // to appear signed in after closing and reopening the browser.
  if (readJson(localStorage, STORAGE_KEY)) {
    removeKey(localStorage, STORAGE_KEY);
    clearAuthTokens();
  }
  clearAuthTokens();
  return null;
}

function writeStoredAuth(user, remember = false) {
  removeKey(sessionStorage, SESSION_STORAGE_KEY);
  removeKey(localStorage, PERSISTENT_STORAGE_KEY);
  const record = {
    user,
    createdAt: Date.now(),
    expiresAt: remember ? Date.now() + PERSISTENT_SESSION_MAX_AGE : null,
  };
  if (remember) localStorage.setItem(PERSISTENT_STORAGE_KEY, JSON.stringify(record));
  else sessionStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(record));
}

function clearStoredAuth() {
  removeKey(sessionStorage, SESSION_STORAGE_KEY);
  removeKey(localStorage, PERSISTENT_STORAGE_KEY);
  removeKey(localStorage, STORAGE_KEY);
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
  const initialAuth = readStoredAuth();
  const [user, setUser] = useState(initialAuth?.user || null);
  const [mode, setMode] = useState(initialAuth?.user?.mode || 'demo');
  const [sessionReady, setSessionReady] = useState(false);

  useEffect(() => {
    let cancelled = false;
    const stored = readStoredAuth();

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

    if (stored.user.mode !== 'api') {
      finish(stored.user, 'demo');
      return () => { cancelled = true; };
    }

    const token = getAccessToken();
    if (!token) {
      clearStoredAuth();
      finish(null, 'demo');
      return () => { cancelled = true; };
    }

    getApiResource('auth/me').then((payload) => {
      const nextUser = { ...payload.user, mode: 'api' };
      writeStoredAuth(nextUser, stored.remember);
      finish(nextUser, 'api');
    }).catch((error) => {
      // Keep a cached session during a temporary network outage, but remove
      // it when Django explicitly says that the session is no longer valid.
      if (error.status === 401 || error.status === 403) {
        clearStoredAuth();
        clearAuthTokens();
        finish(null, 'demo');
      } else {
        finish(stored.user, 'api');
      }
    });

    return () => { cancelled = true; };
  }, []);

  const loginDemo = async (email, password, { remember = false } = {}) => {
    const demoEnabled = String(import.meta.env.VITE_APP_MODE || 'demo').toLowerCase() === 'demo';
    if (!demoEnabled) throw new Error('Demo login is disabled on this deployment.');
    await new Promise((resolve) => setTimeout(resolve, 120));
    const overrides = readDemoPasswordOverrides();
    const account = [...demoAccounts, ...readRegisteredDemoAccounts()].find((item) => item.email.toLowerCase() === email.trim().toLowerCase() && (overrides[item.email.toLowerCase()] || item.password) === password);
    if (!account) throw new Error('Invalid email or password. Use one of the demo accounts shown below.');
    const safeUser = { id: account.id, name: account.name, email: account.email, role: account.role, business: account.business, permissions: permissions[account.role] || ['dashboard'], subscription: { code: account.plan || 'FREE', name: account.plan || 'Free', status: 'Active' }, mode: 'demo' };
    writeStoredAuth(safeUser, remember);
    setUser(safeUser); setMode('demo');
    return safeUser;
  };

  const registerDemo = async ({ name, email, password, businessName, phone }, { remember = false } = {}) => {
    const demoEnabled = String(import.meta.env.VITE_APP_MODE || 'demo').toLowerCase() === 'demo';
    if (!demoEnabled) throw new Error('Demo registration is disabled on this deployment.');
    if (password.length < 8) throw new Error('Password must be at least 8 characters.');
    const accounts = readRegisteredDemoAccounts();
    if ([...demoAccounts, ...accounts].some((item) => item.email.toLowerCase() === email.trim().toLowerCase())) throw new Error('An account with this email already exists.');
    const account = { id: `demo-${Date.now()}`, name: name.trim(), email: email.trim().toLowerCase(), password, role: 'OWNER', business: businessName.trim() || `${name.trim()} Distributors`, phone: phone.trim() };
    localStorage.setItem(REGISTERED_DEMO_KEY, JSON.stringify([...accounts, account]));
    const safeUser = { id: account.id, name: account.name, email: account.email, role: account.role, business: account.business, permissions: permissions[account.role] || ['dashboard'], subscription: { code: 'FREE', name: 'Free', status: 'Trial' }, mode: 'demo' };
    writeStoredAuth(safeUser, remember);
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

  const login = async (email, password, options = {}) => {
    const demoMode = String(import.meta.env.VITE_APP_MODE || 'demo').toLowerCase() === 'demo';
    const fallbackEnabled = demoMode && String(import.meta.env.VITE_DEMO_FALLBACK ?? 'true').toLowerCase() !== 'false';
    try {
      const apiUser = await loginApi(email, password, options);
      const safeUser = { ...apiUser, mode: 'api' };
      writeStoredAuth(safeUser, options.remember);
      setUser(safeUser); setMode('api');
      return safeUser;
    } catch (error) {
      if (!error.network || !fallbackEnabled) throw error;
      return loginDemo(email, password, options);
    }
  };

  const register = async (details, options = {}) => {
    const demoMode = String(import.meta.env.VITE_APP_MODE || 'demo').toLowerCase() === 'demo';
    const fallbackEnabled = demoMode && String(import.meta.env.VITE_DEMO_FALLBACK ?? 'true').toLowerCase() !== 'false';
    try {
      const apiUser = await registerApi(details, options);
      const safeUser = { ...apiUser, mode: 'api' };
      writeStoredAuth(safeUser, options.remember);
      setUser(safeUser); setMode('api');
      return safeUser;
    } catch (error) {
      if (!error.network || !fallbackEnabled) throw error;
      return registerDemo(details, options);
    }
  };

  const logout = async () => {
    try {
      if (mode === 'api') await logoutApi();
    } finally {
      clearStoredAuth();
      clearAuthTokens();
      setUser(null); setMode('demo');
    }
  };

  const updateUser = (nextUser) => {
    const resolvedUser = typeof nextUser === 'function' ? nextUser(user) : nextUser;
    setUser(resolvedUser);
    if (resolvedUser) {
      const stored = readStoredAuth();
      writeStoredAuth(resolvedUser, stored?.remember || false);
    }
  };

  const can = (module) => Boolean(user && (user.permissions || permissions[user.role] || []).includes(module) && planAllows(user.subscription?.code || user.plan, module, user.subscription?.status || 'Active'));
  const value = useMemo(() => ({ user, mode, sessionReady, login, register, loginDemo, registerDemo, resetDemoPassword, logout, can, setUser, updateUser }), [user, mode, sessionReady, updateUser]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider');
  return ctx;
}
