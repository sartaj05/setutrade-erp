import { useEffect, useState } from 'react';
import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';
import CustomerPortalPage from './pages/CustomerPortalPage';
import SupplierPortalPage from './pages/SupplierPortalPage';
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
    window.history.pushState({}, '', to);
    setPath(to);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };
  return { path, navigate };
}

function Routes() {
  const { path, navigate } = useTinyRouter();
  const { user, can } = useAuth();
  const [module, setModule] = useState('dashboard');

  useEffect(() => {
    if (user && !can(module)) setModule('dashboard');
  }, [user, module]);

  if (path === '/portal') return <CustomerPortalPage navigate={navigate} />;
  if (path === '/supplier-portal') return <SupplierPortalPage navigate={navigate} />;

  if (path === '/login') {
    if (user) return <AppShell module={module} onModuleChange={setModule} navigate={navigate}>{module === 'dashboard' ? <DashboardPage /> : <ModulePage module={module} />}</AppShell>;
    return <LoginPage navigate={navigate} />;
  }

  if (path.startsWith('/app')) {
    if (!user) return <LoginPage navigate={navigate} />;
    return <AppShell module={module} onModuleChange={setModule} navigate={navigate}>{module === 'dashboard' ? <DashboardPage /> : <ModulePage module={module} />}</AppShell>;
  }

  return <LandingPage navigate={navigate} path={path} />;
}

export default function App() {
  return <AuthProvider><Routes /></AuthProvider>;
}
