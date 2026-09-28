import { useEffect, useState } from 'react';
import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';
import CustomerPortalPage from './pages/CustomerPortalPage';
import SupplierPortalPage from './pages/SupplierPortalPage';
import PaymentLinkPage from './pages/PaymentLinkPage';
import DashboardPage from './pages/DashboardPage';
import AppShell from './components/AppShell';
import ModulePage from './pages/ModulePage';
import { AuthProvider, useAuth } from './context/AuthContext';

function useTinyRouter() {
  const [path, setPath] = useState(window.location.pathname);
  useEffect(() => {
    const onPop = () => setPath(window.location.pathname);
    window.addEventListener('popstate', onPop);
    return () => window.removeEventListener('popstate', onPop);
  }, []);
  const navigate = (to) => {
    const next = new URL(to, window.location.origin);
    window.history.pushState({}, '', `${next.pathname}${next.search}${next.hash}`);
    setPath(next.pathname);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };
  return { path, navigate };
}

function Routes() {
  const { path, navigate } = useTinyRouter();
  const { user, can, sessionReady } = useAuth();
  const [module, setModule] = useState('dashboard');

  useEffect(() => {
    if (!user || !can(module)) setModule('dashboard');
  }, [user, module]);

  if (!sessionReady) return <div className="session-loading"><div className="session-loading-mark">SS</div><strong>Restoring your workspace…</strong><small>Checking your secure session and role access.</small></div>;

  if (path === '/portal') return <CustomerPortalPage navigate={navigate} />;
  if (path === '/supplier-portal') return <SupplierPortalPage navigate={navigate} />;
  if (path.startsWith('/pay/')) return <PaymentLinkPage token={path.slice(5)} navigate={navigate} />;

  if (path === '/login') {
    return <LoginPage navigate={navigate} />;
  }

  if (path.startsWith('/app')) {
    if (!user) return <LoginPage navigate={navigate} />;
    const activeModule = can(module) ? module : 'dashboard';
    return <AppShell module={activeModule} onModuleChange={setModule} navigate={navigate}>{activeModule === 'dashboard' ? <DashboardPage /> : <ModulePage module={activeModule} />}</AppShell>;
  }

  return <LandingPage navigate={navigate} path={path} />;
}

export default function App() {
  return <AuthProvider><Routes /></AuthProvider>;
}
