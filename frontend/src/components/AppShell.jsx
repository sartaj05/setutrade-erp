import { useEffect, useMemo, useState } from 'react';
import Brand from './Brand';
import Icon from './Icon';
import { permissions } from '../data/demoData';
import { demoNotifications, demoAttention } from '../data/productionData';
import { useAuth } from '../context/AuthContext';
import { getApiResource, healthApi, patchApiResource } from '../services/api';
import AssistantWidget from './AssistantWidget';
import { normalizePlan, PLAN_LABELS, planAllows, requiredPlan } from '../data/plans';

const moduleLabels = {
  dashboard: ['Overview', 'chart'], 'client-workflow': ['Order-to-cash', 'chart'], onboarding: ['Client onboarding', 'users'], 'access-review': ['Role access review', 'shield'], products: ['Products', 'box'], inventory: ['Inventory', 'box'], customers: ['Customers', 'users'],
  orders: ['Orders', 'receipt'], invoices: ['GST Invoices', 'receipt'], purchases: ['Purchases', 'box'], ledger: ['Credit Ledger', 'receipt'],
  warehouses: ['Warehouses', 'box'], barcode: ['Barcode Scan', 'box'], whatsapp: ['WhatsApp Orders', 'receipt'], tax: ['GST & Tax', 'receipt'],
  pricing: ['Price Rules', 'receipt'], returns: ['Returns & Damage', 'box'], 'field-sales': ['Field Sales', 'users'], insights: ['Smart Insights', 'chart'],
  quotations: ['Quotations', 'receipt'], payments: ['Payments', 'receipt'], reports: ['Reports', 'chart'], team: ['Team', 'users'], settings: ['Settings', 'shield'], audit: ['Audit Log', 'shield'], delivery: ['Delivery', 'box'], approvals: ['Approvals', 'shield'], 'invoice-ocr': ['Invoice OCR', 'receipt'], accounting: ['Accounting Sync', 'receipt'], offline: ['Offline Sync', 'shield'], subscription: ['Subscription', 'receipt'], forecasting: ['Forecasting', 'chart'], assistant: ['AI Assistant', 'chart'], collections: ['Collections', 'receipt'], wms: ['Advanced WMS', 'box'], 'supplier-portal-admin': ['Supplier Portal', 'users'], automations: ['Automation', 'shield'], channels: ['Sales Channels', 'receipt'], 'distribution-network': ['Distributor Network', 'chart'], crm: ['CRM Pipeline', 'users'], schemes: ['Schemes & Claims', 'receipt'], 'gst-cockpit': ['GST Cockpit', 'shield'], 'procurement-intelligence': ['Smart Procurement', 'box'], 'fleet-routes': ['Fleet & Routes', 'box'], 'credit-risk': ['Credit Risk', 'shield'], 'security-center': ['Security Center', 'shield'], integrations: ['Integration Hub', 'shield'], 'executive-bi': ['Executive BI', 'chart'], 'copilot-actions': ['AI Action Copilot', 'shield'], 'product-master': ['Product Master', 'box'], traceability: ['Traceability', 'box'], treasury: ['Treasury', 'receipt'], contracts: ['Contracts', 'receipt'], quality: ['Quality Control', 'shield'], 'supply-planning': ['Supply Planning', 'chart'], 'service-rma': ['Warranty & RMA', 'users'], expenses: ['Expenses', 'receipt'], 'report-builder': ['Report Builder', 'chart'], 'operations-center': ['Ops Control', 'shield'],
};

const navigationGroups = [
  { label: 'Overview', keys: ['dashboard'] },
  { label: 'Sales & customers', keys: ['client-workflow', 'customers', 'orders', 'quotations', 'whatsapp', 'pricing', 'crm', 'field-sales', 'channels', 'collections', 'delivery', 'service-rma', 'contracts', 'schemes'] },
  { label: 'Inventory & fulfilment', keys: ['products', 'inventory', 'purchases', 'warehouses', 'barcode', 'returns', 'wms', 'invoice-ocr', 'procurement-intelligence', 'fleet-routes', 'traceability', 'quality', 'supply-planning', 'product-master'] },
  { label: 'Finance & compliance', keys: ['invoices', 'ledger', 'payments', 'tax', 'gst-cockpit', 'accounting', 'treasury', 'expenses', 'credit-risk', 'reports', 'report-builder', 'audit'] },
  { label: 'Intelligence & admin', keys: ['onboarding', 'access-review', 'insights', 'forecasting', 'assistant', 'automations', 'distribution-network', 'supplier-portal-admin', 'approvals', 'team', 'settings', 'subscription', 'offline', 'operations-center', 'security-center', 'integrations', 'executive-bi', 'copilot-actions'] },
];

export default function AppShell({ module, onModuleChange, children, navigate }) {
  const { user, mode, logout } = useAuth();
  const roleModules = user.permissions || permissions[user.role] || ['dashboard'];
  const plan = normalizePlan(user.subscription?.code || user.plan);
  const visibleModules = roleModules.filter((key) => planAllows(plan, key));
  const lockedModules = roleModules.filter((key) => !planAllows(plan, key));
  const initials = user.name.split(' ').map((x) => x[0]).slice(0, 2).join('');
  const [search, setSearch] = useState(''); const [searchResults, setSearchResults] = useState([]); const [showSearch, setShowSearch] = useState(false);
  const [notifications, setNotifications] = useState(demoNotifications); const [showNotifications, setShowNotifications] = useState(false);
  const [apiHealth, setApiHealth] = useState(mode === 'api' ? 'checking' : 'demo');
  const [planNotice, setPlanNotice] = useState('');

  useEffect(() => {
    if (mode !== 'api') { setNotifications([...demoAttention.items, ...demoNotifications]); setApiHealth('demo'); return; }
    setApiHealth('checking');
    healthApi().then((payload) => setApiHealth(payload.ok && payload.database === 'ok' ? 'online' : 'degraded')).catch(() => setApiHealth('offline'));
    Promise.all([getApiResource('notifications'), getApiResource('attention')]).then(([noticeData, attentionData]) => {
      const alerts = (attentionData.items || []).map((item) => ({ ...item, read: false, time: item.createdAt || 'Recently' }));
      setNotifications([...alerts, ...(noticeData.notifications || [])]);
    }).catch(() => {});
  }, [mode]);

  useEffect(() => {
    if (mode !== 'api' || search.trim().length < 2) { setSearchResults([]); return; }
    const id = setTimeout(() => getApiResource('search', `q=${encodeURIComponent(search.trim())}`).then((x) => setSearchResults(x.results || [])).catch(() => setSearchResults([])), 220);
    return () => clearTimeout(id);
  }, [search, mode]);

  useEffect(() => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, [module]);

  const unread = useMemo(() => notifications.filter((n) => !n.read).length, [notifications]);
  const signOut = async () => { await logout(); navigate('/login'); };
  const pickSearch = (item) => { if (visibleModules.includes(item.module)) onModuleChange(item.module); setSearch(''); setShowSearch(false); };
  const markAllRead = async () => { if (mode === 'api') { try { await patchApiResource('notifications/', { all: true }); } catch {} } setNotifications((rows) => rows.map((n) => ({ ...n, read: true }))); };

  return (
    <div className="app-layout">
      <aside className="sidebar">
        <div className="sidebar-brand"><Brand /></div>
        <nav className="side-nav">
          {navigationGroups.map((group) => {
            const items = group.keys.filter((key) => roleModules.includes(key) && moduleLabels[key]);
            if (!items.length) return null;
            return <div className="side-nav-group" key={group.label}><span className="side-nav-label">{group.label}</span>{items.map((key) => { const [label, icon] = moduleLabels[key]; const locked = !planAllows(plan, key); return <button className={`${module === key ? 'side-link active' : 'side-link'}${locked ? ' locked' : ''}`} key={key} onClick={() => { if (locked) { setPlanNotice(`${label} requires the ${PLAN_LABELS[requiredPlan(key)]} plan.`); return; } onModuleChange(key); }} title={locked ? `Requires ${PLAN_LABELS[requiredPlan(key)]}` : label}><Icon name={icon} size={18} /><span>{label}</span>{locked && <em>Upgrade</em>}</button>; })}</div>;
          })}
        </nav>
        <div className="sidebar-bottom"><div className="mode-chip"><span className={apiHealth === 'online' ? 'online' : ''} /> {mode !== 'api' ? 'Safe demo mode' : apiHealth === 'checking' ? 'Checking production API…' : apiHealth === 'online' ? 'Production API connected' : apiHealth === 'degraded' ? 'Production API degraded' : 'Production API unavailable'}</div><button className="signout" onClick={signOut}>Sign out</button></div>
      </aside>

      <section className="app-main">
        <header className="app-topbar">
          <div className="top-title"><small>{user.business}</small><strong>{moduleLabels[module]?.[0] || 'Overview'}</strong></div>
          <div className="global-search"><input value={search} onFocus={() => setShowSearch(true)} onChange={(e) => { setSearch(e.target.value); setShowSearch(true); }} placeholder="Search SKU, customer, order, invoice…" />{showSearch && search.trim().length >= 2 && <div className="search-popover">{mode !== 'api' && <div className="search-empty">Global search uses the live Django database.</div>}{mode === 'api' && searchResults.length === 0 && <div className="search-empty">No matches yet.</div>}{searchResults.map((r) => <button key={`${r.type}-${r.id}`} onClick={() => pickSearch(r)}><span>{r.type}</span><strong>{r.label}</strong><small>{r.meta}</small></button>)}</div>}</div>
          <div className="top-actions"><button className="notification-btn" onClick={() => setShowNotifications((v) => !v)}>◉{unread > 0 && <b>{unread}</b>}</button>{showNotifications && <div className="notification-popover"><header><strong>Notifications</strong><button onClick={markAllRead}>Mark all read</button></header>{notifications.slice(0, 8).map((n) => <button key={n.id} className={n.read ? 'read' : ''} onClick={() => { if (n.module && visibleModules.includes(n.module)) onModuleChange(n.module); setShowNotifications(false); }}><i className={`notice-dot ${n.level}`} /><span><strong>{n.title}</strong><small>{n.message}</small></span></button>)}</div>}<div className="user-menu"><div className="top-role"><span>{user.role}</span><small>{user.name}</small></div><div className="user-avatar">{initials}</div></div></div>
        </header>
        <main className="app-content">{mode === 'api' && apiHealth === 'offline' && <div className="production-warning"><strong>Production API unavailable</strong><span>Live records are paused. Demo data will not be shown.</span><button onClick={() => window.location.reload()}>Retry</button></div>}{planNotice && <div className="plan-notice"><strong>{PLAN_LABELS[plan]} plan</strong><span>{planNotice}</span><button onClick={() => { setPlanNotice(''); onModuleChange('subscription'); }}>View plans</button><button className="plan-notice-close" onClick={() => setPlanNotice('')}>×</button></div>}{children}</main>
      </section>
      <AssistantWidget hidden={module === 'assistant'} navigate={navigate} onModuleChange={onModuleChange} visibleModules={visibleModules} />
    </div>
  );
}
