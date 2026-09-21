import Brand from './Brand';
import Icon from './Icon';
import { permissions } from '../data/demoData';
import { useAuth } from '../context/AuthContext';

const moduleLabels = {
  dashboard: ['Overview', 'chart'],
  products: ['Products', 'box'],
  inventory: ['Inventory', 'box'],
  customers: ['Customers', 'users'],
  orders: ['Orders', 'receipt'],
  invoices: ['GST Invoices', 'receipt'],
  purchases: ['Purchases', 'box'],
  quotations: ['Quotations', 'receipt'],
  payments: ['Payments', 'receipt'],
  reports: ['Reports', 'chart'],
  team: ['Team', 'users'],
  settings: ['Settings', 'shield'],
};

export default function AppShell({ module, onModuleChange, children, navigate }) {
  const { user, mode, logout } = useAuth();
  const visibleModules = permissions[user.role] || ['dashboard'];
  const initials = user.name.split(' ').map((x) => x[0]).slice(0, 2).join('');

  const signOut = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="app-layout">
      <aside className="sidebar">
        <div className="sidebar-brand"><Brand /></div>
        <nav className="side-nav">
          {visibleModules.map((key) => {
            const [label, icon] = moduleLabels[key];
            return <button className={module === key ? 'side-link active' : 'side-link'} key={key} onClick={() => onModuleChange(key)}><Icon name={icon} size={18} /><span>{label}</span></button>;
          })}
        </nav>
        <div className="sidebar-bottom">
          <div className="mode-chip"><span className={mode === 'api' ? 'online' : ''} /> {mode === 'api' ? 'API connected' : 'Demo data mode'}</div>
          <button className="signout" onClick={signOut}>Sign out</button>
        </div>
      </aside>

      <section className="app-main">
        <header className="app-topbar">
          <div><small>{user.business}</small><strong>{moduleLabels[module]?.[0] || 'Overview'}</strong></div>
          <div className="user-menu"><div className="top-role"><span>{user.role}</span><small>{user.name}</small></div><div className="user-avatar">{initials}</div></div>
        </header>
        <main className="app-content">{children}</main>
      </section>
    </div>
  );
}
