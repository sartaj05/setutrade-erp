import { createContext, useContext, useMemo, useState } from 'react';
import { demoAccounts, permissions } from '../data/demoData';
import { loginApi } from '../services/api';

const AuthContext = createContext(null);
const STORAGE_KEY = 'setustock_auth';

function readStoredUser() {
  try { return JSON.parse(localStorage.getItem(STORAGE_KEY)) || null; }
  catch { return null; }
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(readStoredUser);
  const [mode, setMode] = useState(user?.mode || 'demo');

  const loginDemo = async (email, password) => {
    await new Promise((resolve) => setTimeout(resolve, 180));
    const account = demoAccounts.find((item) => item.email.toLowerCase() === email.trim().toLowerCase() && item.password === password);
    if (!account) throw new Error('Invalid email or password. Use one of the demo accounts shown below.');
    const safeUser = { id: account.id, name: account.name, email: account.email, role: account.role, business: account.business, mode: 'demo' };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(safeUser));
    setUser(safeUser); setMode('demo');
    return safeUser;
  };

  const login = async (email, password) => {
    const fallbackEnabled = String(import.meta.env.VITE_DEMO_FALLBACK ?? 'true').toLowerCase() !== 'false';
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

  const logout = () => {
    localStorage.removeItem(STORAGE_KEY);
    localStorage.removeItem('setustock_token');
    setUser(null); setMode('demo');
  };

  const can = (module) => Boolean(user && permissions[user.role]?.includes(module));
  const value = useMemo(() => ({ user, mode, login, loginDemo, logout, can }), [user, mode]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider');
  return ctx;
}
