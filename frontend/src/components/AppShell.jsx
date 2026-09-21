import { useEffect, useMemo, useState } from 'react';
import Brand from './Brand';
import Icon from './Icon';
import { permissions } from '../data/demoData';
import { demoNotifications } from '../data/productionData';
import { useAuth } from '../context/AuthContext';
import { getApiResource, patchApiResource } from '../services/api';

const moduleLabels = {
  dashboard: ['Overview', 'chart'], products: ['Products', 'box'], inventory: ['Inventory', 'box'], customers: ['Customers', 'users'],
  orders: ['Orders', 'receipt'], invoices: ['GST Invoices', 'receipt'], purchases: ['Purchases', 'box'], ledger: ['Credit Ledger', 'receipt'],
  warehouses: ['Warehouses', 'box'], barcode: ['Barcode Scan', 'box'], whatsapp: ['WhatsApp Orders', 'receipt'], tax: ['GST & Tax', 'receipt'],
  pricing: ['Price Rules', 'receipt'], returns: ['Returns & Damage', 'box'], 'field-sales': ['Field Sales', 'users'], insights: ['Smart Insights', 'chart'],
  quotations: ['Quotations', 'receipt'], payments: ['Payments', 'receipt'], reports: ['Reports', 'chart'], team: ['Team', 'users'], settings: ['Settings', 'shield'], audit: ['Audit Log', 'shield'], delivery: ['Delivery', 'box'], approvals: ['Approvals', 'shield'], 'invoice-ocr': ['Invoice OCR', 'receipt'], accounting: ['Accounting Sync', 'receipt'], offline: ['Offline Sync', 'shield'], subscription: ['Subscription', 'receipt'], forecasting: ['Forecasting', 'chart'], assistant: ['AI Assistant', 'chart'], collections: ['Collections', 'receipt'], wms: ['Advanced WMS', 'box'], 'supplier-portal-admin': ['Supplier Portal', 'users'], automations: ['Automation', 'shield'], channels: ['Sales Channels', 'receipt'], 'distribution-network': ['Distributor Network', 'chart'],
};

export default function AppShell({ module, onModuleChange, children, navigate }) {
  const { user, mode, logout } = useAuth();
  const visibleModules = user.permissions || permissions[user.role] || ['dashboard'];
  const initials = user.name.split(' ').map((x) => x[0]).slice(0, 2).join('');
  const [search, setSearch] = useState(''); const [searchResults, setSearchResults] = useState([]); const [showSearch, setShowSearch] = useState(false);
  const [notifications, setNotifications] = useState(demoNotifications); const [showNotifications, setShowNotifications] = useState(false);

  useEffect(() => {
    if (mode !== 'api') { setNotifications(demoNotifications); return; }
    getApiResource('notifications').then((x) => setNotifications(x.notifications || [])).catch(() => {});
  }, [mode]);

  useEffect(() => {
    if (mode !== 'api' || search.trim().length < 2) { setSearchResults([]); return; }
    const id = setTimeout(() => getApiResource('search', `q=${encodeURIComponent(search.trim())}`).then((x) => setSearchResults(x.results || [])).catch(() => setSearchResults([])), 220);
    return () => clearTimeout(id);
  }, [search, mode]);

  const unread = useMemo(() => notifications.filter((n) => !n.read).length, [notifications]);
  const signOut = async () => { await logout(); navigate('/login'); };
  const pickSearch = (item) => { if (visibleModules.includes(item.module)) onModuleChange(item.module); setSearch(''); setShowSearch(false); };
  const markAllRead = async () => { if (mode === 'api') { try { await patchApiResource('notifications/', { all: true }); } catch {} } setNotifications((rows) => rows.map((n) => ({ ...n, read: true }))); };

  return (
    <div className="app-layout">
      <aside className="sidebar">
        <div className="sidebar-brand"><Brand /></div>
        <nav className="side-nav">
          {visibleModules.filter((key) => moduleLabels[key]).map((key) => { const [label, icon] = moduleLabels[key]; return <button className={module === key ? 'side-link active' : 'side-link'} key={key} onClick={() => onModuleChange(key)}><Icon name={icon} size={18} /><span>{label}</span></button>; })}
        </nav>
        <div className="sidebar-bottom"><div className="mode-chip"><span className={mode === 'api' ? 'online' : ''} /> {mode === 'api' ? 'Production API connected' : 'Safe demo mode'}</div><button className="signout" onClick={signOut}>Sign out</button></div>
      </aside>

      <section className="app-main">
        <header className="app-topbar">
          <div className="top-title"><small>{user.business}</small><strong>{moduleLabels[module]?.[0] || 'Overview'}</strong></div>
          <div className="global-search"><input value={search} onFocus={() => setShowSearch(true)} onChange={(e) => { setSearch(e.target.value); setShowSearch(true); }} placeholder="Search SKU, customer, order, invoice…" />{showSearch && search.trim().length >= 2 && <div className="search-popover">{mode !== 'api' && <div className="search-empty">Global search uses the live Django database.</div>}{mode === 'api' && searchResults.length === 0 && <div className="search-empty">No matches yet.</div>}{searchResults.map((r) => <button key={`${r.type}-${r.id}`} onClick={() => pickSearch(r)}><span>{r.type}</span><strong>{r.label}</strong><small>{r.meta}</small></button>)}</div>}</div>
          <div className="top-actions"><button className="notification-btn" onClick={() => setShowNotifications((v) => !v)}>◉{unread > 0 && <b>{unread}</b>}</button>{showNotifications && <div className="notification-popover"><header><strong>Notifications</strong><button onClick={markAllRead}>Mark all read</button></header>{notifications.slice(0, 8).map((n) => <button key={n.id} className={n.read ? 'read' : ''} onClick={() => { if (n.module && visibleModules.includes(n.module)) onModuleChange(n.module); setShowNotifications(false); }}><i className={`notice-dot ${n.level}`} /><span><strong>{n.title}</strong><small>{n.message}</small></span></button>)}</div>}<div className="user-menu"><div className="top-role"><span>{user.role}</span><small>{user.name}</small></div><div className="user-avatar">{initials}</div></div></div>
        </header>
        <main className="app-content">{children}</main>
      </section>
    </div>
  );
}
