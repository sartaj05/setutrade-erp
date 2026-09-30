import { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { createApiResource, getApiResource } from '../services/api';
import { queueOfflineEvent, listOfflineEvents, removeOfflineEvents } from '../services/offlineQueue';
import {
  demoDelivery, demoApprovals, demoCaptures, demoAccounting, demoOffline,
  demoSubscription, demoForecasts, demoAssistant,
} from '../data/growthData';
import LiveDeliveryPage from './LiveDeliveryPage';
import AIForecastingPage from './AIForecastingPage';

const money = (n) => `₹${Number(n || 0).toLocaleString('en-IN')}`;
const Notice = ({ text }) => text ? <div className="inline-notice">{text}</div> : null;

function DeliveryPage({ mode, notice, setNotice }) {
  const deliver = async (stop) => {
    try {
      const receiverName = window.prompt('Receiver name', 'Demo receiver') || '';
      const signature = window.prompt('Proof reference or signature', 'signed-at-door') || '';
      if (!receiverName || !signature) return setNotice('Receiver name and proof are required for e-POD.');
      if (mode === 'api') await createApiResource('delivery', { action: 'deliver', stopId: stop.id, otpVerified: true, receiverName, signature });
      setNotice(mode === 'api' ? 'Delivery marked complete.' : 'Demo e-POD captured locally.');
    } catch (e) { setNotice(e.message); }
  };
  return <div>
    <div className="module-header"><div><span className="eyebrow">Dispatch control</span><h1>Delivery & e-POD</h1><p>Plan vehicle runs, track COD and capture OTP, signature or photo proof at the customer door.</p></div><button onClick={() => setNotice('Create-run flow is API-ready for dispatched orders.')}>New delivery run</button></div>
    <Notice text={notice}/>
    <div className="report-grid"><article><span>Runs today</span><strong>7</strong><small>3 currently on road</small></article><article><span>Stops</span><strong>31</strong><small>22 delivered</small></article><article><span>COD planned</span><strong>{money(118600)}</strong><small>{money(42800)} pending</small></article><article><span>Success rate</span><strong>94%</strong><small>last 30 days</small></article></div>
    {demoDelivery.runs.map((r) => <article className="panel module-panel" key={r.id}><div className="panel-head"><div><span>{r.runNo}</span><h3>{r.route}</h3><small>{r.driver} · {r.vehicle} · {r.status}</small></div></div><div className="table-wrap"><table className="data-table module-table"><thead><tr><th>Seq</th><th>Order</th><th>Customer</th><th>COD</th><th>Status</th><th>e-POD</th></tr></thead><tbody>{r.stops.map((s) => <tr key={s.id}><td>{s.sequence}</td><td>{s.order}</td><td>{s.customer}</td><td>{money(s.cod)}</td><td>{s.status}</td><td><button className="table-action" disabled={s.status === 'Delivered'} onClick={() => deliver(s)}>{s.status === 'Delivered' ? 'Captured' : 'Mark delivered'}</button></td></tr>)}</tbody></table></div></article>)}
  </div>;
}

function LegacyApprovalPage({ mode, notice, setNotice }) {
  const decide = async (row, action) => {
    try { if (mode === 'api') await createApiResource('approvals', { id: row.id, action }); setNotice(`${action === 'approve' ? 'Approved' : 'Rejected'} ${row.requestNo}.`); }
    catch (e) { setNotice(e.message); }
  };
  return <div><div className="module-header"><div><span className="eyebrow">Exception control</span><h1>Approval workflows</h1><p>Route high discounts, credit overrides, returns and sensitive transactions to the correct approver.</p></div><button onClick={() => setNotice('Policy editor is company-scoped and API-ready.')}>Manage policies</button></div><Notice text={notice}/><div className="report-grid">{demoApprovals.policies.map((p) => <article key={p.key}><span>{p.label}</span><strong>{p.approverRole}</strong><small>{p.active ? 'Policy active' : 'Disabled'}</small></article>)}</div><article className="panel module-panel"><div className="table-wrap"><table className="data-table module-table"><thead><tr><th>Request</th><th>Reason</th><th>Requested by</th><th>Amount</th><th>Status</th><th>Decision</th></tr></thead><tbody>{demoApprovals.requests.map((r) => <tr key={r.id}><td>{r.requestNo}</td><td><strong>{r.title}</strong><small>{r.entity}</small></td><td>{r.requestedBy}</td><td>{money(r.amount)}</td><td>{r.status}</td><td>{r.status === 'Pending' ? <div className="row-actions"><button className="table-action" onClick={() => decide(r, 'approve')}>Approve</button><button className="table-action" onClick={() => decide(r, 'reject')}>Reject</button></div> : '—'}</td></tr>)}</tbody></table></div></article></div>;
}

function ApprovalPage({ mode, notice, setNotice }) {
  const { user } = useAuth();
  const [data, setData] = useState(demoApprovals);
  const [requestOpen, setRequestOpen] = useState(false);
  const [policyOpen, setPolicyOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const load = async () => { if (mode === 'api') { try { setData(await getApiResource('approvals')); } catch (e) { setNotice(e.message); } } else setData(demoApprovals); };
  useEffect(() => { load(); }, [mode]);
  const decide = async (row, action) => {
    try { const note = window.prompt(`${action === 'approve' ? 'Approval' : 'Rejection'} note (optional):`, '') || ''; if (mode === 'api') await createApiResource('approvals', { id: row.id, action, note }); setNotice(`${action === 'approve' ? 'Approved' : 'Rejected'} ${row.requestNo}.`); load(); }
    catch (e) { setNotice(e.message); }
  };
  const submitRequest = async (event) => {
    event.preventDefault(); setBusy(true); const form = Object.fromEntries(new FormData(event.currentTarget).entries());
    try { if (mode === 'api') await createApiResource('approvals', { action: 'request', policyKey: form.policyKey, entityType: form.entityType, entityId: form.entityId, title: form.title, amount: Number(form.amount || 0), payload: { note: form.note } }); setNotice(mode === 'api' ? 'Approval request submitted and routed to the configured approver.' : 'Demo approval request created.'); setRequestOpen(false); load(); }
    catch (e) { setNotice(e.message); } finally { setBusy(false); }
  };
  const savePolicy = async (event) => {
    event.preventDefault(); setBusy(true); const form = Object.fromEntries(new FormData(event.currentTarget).entries());
    try { if (mode === 'api') await createApiResource('approvals', { action: 'policy', key: form.key, label: form.label, threshold: Number(form.threshold || 0), approverRole: form.approverRole, active: true }); setNotice(mode === 'api' ? 'Approval policy saved.' : 'Demo approval policy saved.'); setPolicyOpen(false); load(); }
    catch (e) { setNotice(e.message); } finally { setBusy(false); }
  };
  const policies = data.policies || []; const requests = data.requests || [];
  return <div><div className="module-header"><div><span className="eyebrow">Exception control</span><h1>Approval workflows</h1><p>Route discounts, credit limits, refunds, stock adjustments and plan changes to the right approver with a permanent audit trail.</p></div><div className="row-actions"><button onClick={() => setRequestOpen((v) => !v)}>New request</button>{user.role === 'OWNER' && <button className="secondary-btn" onClick={() => setPolicyOpen((v) => !v)}>Manage policies</button>}</div></div><Notice text={notice}/><div className="report-grid">{policies.map((p) => <article key={p.key}><span>{p.label}</span><strong>{p.approverRole}</strong><small>{p.active ? `Approval above ${money(p.threshold)}` : 'Disabled'}</small></article>)}</div>{requestOpen && <article className="panel module-panel"><div className="panel-head"><div><span>Controlled action</span><h3>Submit approval request</h3></div></div><form className="smart-form" onSubmit={submitRequest}><label>Rule<select name="policyKey" required>{policies.filter((p) => p.active).map((p) => <option key={p.key} value={p.key}>{p.label}</option>)}</select></label><label>Entity type<input name="entityType" defaultValue="Order" required/></label><label>Entity ID<input name="entityId" placeholder="SO-1099" required/></label><label>Title<input name="title" placeholder="18% discount for dealer" required/></label><label>Amount<input name="amount" type="number" min="0" step="0.01" defaultValue="0"/></label><label className="full-field">Context<textarea name="note" placeholder="Why this exception is needed"/></label><div className="form-actions"><button type="button" className="secondary-btn" onClick={() => setRequestOpen(false)}>Cancel</button><button disabled={busy}>{busy ? 'Submitting…' : 'Submit request'}</button></div></form></article>}{policyOpen && <article className="panel module-panel"><div className="panel-head"><div><span>Owner control</span><h3>Save approval policy</h3></div></div><form className="smart-form" onSubmit={savePolicy}><label>Rule key<input name="key" defaultValue="discount" required/></label><label>Label<input name="label" defaultValue="Discount above 10%" required/></label><label>Threshold<input name="threshold" type="number" min="0" step="0.01" defaultValue="10" required/></label><label>Approver<select name="approverRole" defaultValue="MANAGER"><option>MANAGER</option><option>OWNER</option></select></label><div className="form-actions"><button type="button" className="secondary-btn" onClick={() => setPolicyOpen(false)}>Cancel</button><button disabled={busy}>{busy ? 'Saving…' : 'Save policy'}</button></div></form></article>}<article className="panel module-panel"><div className="panel-head"><div><span>Review queue</span><h3>Requests and decisions</h3></div><small>Every request, decision and policy change is written to Audit Log.</small></div><div className="table-wrap"><table className="data-table module-table"><thead><tr><th>Request</th><th>Reason</th><th>Requested by</th><th>Amount</th><th>Status</th><th>Decision</th></tr></thead><tbody>{requests.map((r) => <tr key={r.id}><td><strong>{r.requestNo}</strong><small>{r.entity} {r.entityId ? `· ${r.entityId}` : ''}</small></td><td>{r.title}<small>{r.decisionNote || r.approverRole}</small></td><td>{r.requestedBy}</td><td>{money(r.amount)}</td><td>{r.status}</td><td>{r.status === 'Pending' ? <div className="row-actions"><button className="table-action" onClick={() => decide(r, 'approve')}>Approve</button><button className="table-action" onClick={() => decide(r, 'reject')}>Reject</button></div> : <small>{r.decidedBy || 'Auto-approved'}</small>}</td></tr>)}</tbody></table></div></article></div>;
}

function InvoiceOcrPage({ mode, notice, setNotice }) {
  const [raw, setRaw] = useState('Invoice No: PC-19024\nGSTIN 07AAACP6471B1Z7\nDate 21/09/2026\nGrand Total ₹ 48,760.00');
  const [rows, setRows] = useState(demoCaptures);
  const extract = async () => {
    try {
      if (mode === 'api') { const result = await createApiResource('invoice-ocr', { fileName: 'uploaded-invoice.txt', rawText: raw }); setRows((r) => [result.capture, ...r]); }
      else setRows((r) => [{ id: Date.now(), fileName: 'demo-upload.pdf', supplier: 'Auto matched supplier', status: 'Extracted', confidence: 88, data: { invoiceNumber: 'PC-19024', gstin: '07AAACP6471B1Z7', invoiceDate: '21/09/2026', total: 48760 } }, ...r]);
      setNotice('Invoice fields extracted for human review.');
    } catch (e) { setNotice(e.message); }
  };
  return <div><div className="module-header"><div><span className="eyebrow">Accounts automation</span><h1>Purchase invoice OCR</h1><p>Upload or paste supplier invoice text, extract key fields, then review before creating accounting entries.</p></div></div><Notice text={notice}/><div className="two-col-grid"><article className="panel module-panel"><div className="panel-head"><div><span>OCR workbench</span><h3>Extract invoice</h3></div></div><textarea style={{ width: '100%', minHeight: 180 }} value={raw} onChange={(e) => setRaw(e.target.value)}/><button style={{ marginTop: 12 }} onClick={extract}>Extract fields</button></article><article className="panel module-panel"><div className="panel-head"><div><span>Control</span><h3>Human review required</h3></div></div><p>OCR never posts a purchase automatically. Staff verify supplier, GST, line items and totals first.</p></article></div><article className="panel module-panel"><div className="table-wrap"><table className="data-table module-table"><thead><tr><th>File</th><th>Supplier</th><th>Invoice</th><th>Total</th><th>Confidence</th><th>Status</th></tr></thead><tbody>{rows.map((x) => <tr key={x.id}><td>{x.fileName}</td><td>{x.supplier}</td><td>{x.data?.invoiceNumber || '—'}</td><td>{money(x.data?.total)}</td><td>{x.confidence}%</td><td>{x.status}</td></tr>)}</tbody></table></div></article></div>;
}

function AccountingPage({ mode, notice, setNotice }) {
  const [jobs, setJobs] = useState(demoAccounting.jobs);
  const run = async () => {
    try {
      if (mode === 'api') { const result = await createApiResource('accounting', { action: 'export', from: '2026-09-01', to: new Date().toISOString().slice(0, 10) }); setJobs((r) => [result.job, ...r]); }
      else setJobs((r) => [{ id: Date.now(), exportNo: 'ACC-DEMO', provider: 'CSV', from: '2026-09-01', to: '2026-09-21', voucherCount: 172, status: 'Ready' }, ...r]);
      setNotice('Accounting voucher pack generated.');
    } catch (e) { setNotice(e.message); }
  };
  const sync = async () => { try { if (mode === 'api') { const result = await createApiResource('accounting', { action: 'sync', from: '2026-09-01', to: new Date().toISOString().slice(0, 10) }); setJobs((r) => [result.job, ...r]); setNotice(result.message); } else setNotice('Demo connector sync completed.'); } catch (e) { setNotice(e.message); } };
  return <div><div className="module-header"><div><span className="eyebrow">Books bridge</span><h1>Accounting integration</h1><p>Prepare sales, purchase, receipt and payment vouchers for Tally, Zoho Books or accountant-friendly CSV export.</p></div><div className="row-actions"><button className="secondary-btn" onClick={run}>Generate export</button><button onClick={sync}>Sync connector</button></div></div><Notice text={notice}/><div className="report-grid"><article><span>Connector</span><strong>Tally / CSV</strong><small>credential-free demo mode</small></article><article><span>Voucher types</span><strong>4</strong><small>sales, purchase, receipt, payment</small></article><article><span>Last pack</span><strong>318</strong><small>vouchers</small></article></div><article className="panel module-panel"><div className="table-wrap"><table className="data-table module-table"><thead><tr><th>Export</th><th>Provider</th><th>Period</th><th>Vouchers</th><th>Status</th></tr></thead><tbody>{jobs.map((j) => <tr key={j.id}><td>{j.exportNo}</td><td>{j.provider}</td><td>{j.from} → {j.to}</td><td>{j.voucherCount}</td><td>{j.status}</td></tr>)}</tbody></table></div></article></div>;
}

function OfflinePage({ mode, notice, setNotice }) {
  const [online, setOnline] = useState(navigator.onLine);
  const [queue, setQueue] = useState(demoOffline.queue);
  useEffect(() => {
    const update = () => setOnline(navigator.onLine);
    window.addEventListener('online', update); window.addEventListener('offline', update);
    listOfflineEvents().then((items) => { if (items.length) setQueue(items.map((e) => ({ ...e, summary: e.payload?.notes || e.type }))); }).catch(() => {});
    return () => { window.removeEventListener('online', update); window.removeEventListener('offline', update); };
  }, []);
  const add = async () => { const e = await queueOfflineEvent('sales-visit', { notes: 'Offline customer follow-up', date: new Date().toISOString().slice(0, 10) }); setQueue((q) => [...q, { ...e, summary: 'Offline customer follow-up' }]); setNotice('Saved on this device. It will survive refreshes.'); };
  const sync = async () => {
    if (!navigator.onLine) { setNotice('Still offline. Queue kept safely on this device.'); return; }
    try { const local = await listOfflineEvents(); if (mode === 'api' && local.length) { const result = await createApiResource('sync/offline', { deviceId: 'web-pwa', events: local }); await removeOfflineEvents(result.results.filter((x) => ['synced', 'duplicate'].includes(x.status)).map((x) => x.id)); } setQueue([]); setNotice('Offline queue synchronized.'); }
    catch (e) { setNotice(e.message); }
  };
  return <div><div className="module-header"><div><span className="eyebrow">Resilient field work</span><h1>Offline Sales / PWA</h1><p>Cache the app shell, queue field actions in IndexedDB and replay them safely when connectivity returns.</p></div><button onClick={sync}>Sync now</button></div><Notice text={notice}/><div className="report-grid"><article><span>Connection</span><strong>{online ? 'Online' : 'Offline'}</strong><small>browser network state</small></article><article><span>Queued actions</span><strong>{queue.length}</strong><small>device-resident</small></article><article><span>Cached datasets</span><strong>{demoOffline.cached.length}</strong><small>{demoOffline.cached.join(', ')}</small></article></div><article className="panel module-panel"><div className="panel-head"><div><span>Offline queue</span><h3>Pending device actions</h3></div><button onClick={add}>Simulate offline visit</button></div>{queue.length ? queue.map((x) => <div className="list-row" key={x.id}><strong>{x.type}</strong><span>{x.summary}</span><small>{x.createdAt || x.created_at}</small></div>) : <p className="muted">No pending actions.</p>}</article></div>;
}

function SubscriptionPage({ mode, notice, setNotice }) {
  const { user, setUser } = useAuth();
  const [live, setLive] = useState(null);
  useEffect(() => { setLive(null); if (mode === 'api') getApiResource('subscription').then(setLive).catch(() => {}); }, [mode]);
  const change = async (plan) => { try { if (mode === 'api') { const result = await createApiResource('subscription', { action: 'change-plan', planCode: plan.code }); if (result.checkout) { setNotice(result.checkout.providerConfigured ? `Checkout order ${result.checkout.orderId} created. Complete payment to activate ${plan.name}.` : 'Billing provider is not configured yet. Add provider credentials and webhook secret before accepting live payments.'); return; } const next = await getApiResource('subscription'); setLive(next); if (user) setUser({ ...user, subscription: next.subscription }); } setNotice(`Plan changed to ${plan.name}.`); } catch (e) { setNotice(e.message); } };
  const d = live || demoSubscription;
  const limits = d.limits || { users: 0, products: 0, branches: 0, warehouses: 0, orders: 0 };
  const currentCode = d.subscription.publicCode || d.subscription.plan || d.subscription.code;
  const limit = (plan, key, legacy) => plan.limits?.[key] ?? plan[legacy] ?? '—';
  return <div><div className="module-header"><div><span className="eyebrow">SaaS commercial layer</span><h1>Subscription billing</h1><p>Control trials, plan limits, recurring billing state and SaaS invoices per client company.</p></div></div><Notice text={notice}/><div className="report-grid"><article><span>Current plan</span><strong>{d.subscription.planName || d.subscription.name}</strong><small>{d.subscription.status} · ends {d.subscription.periodEnd || 'No expiry'}</small></article><article><span>Users</span><strong>{d.usage.users} / {limits.users || '—'}</strong><small>active team members</small></article><article><span>Products</span><strong>{d.usage.products ?? 0} / {limits.products || '—'}</strong><small>active catalogue SKUs</small></article><article><span>Orders this month</span><strong>{d.usage.orders ?? 0} / {limits.orders || '—'}</strong><small>monthly plan allowance</small></article></div><div className="plan-grid">{d.plans.map((p) => { const isCurrent = p.publicCode === currentCode || p.code === currentCode; return <article className={`panel ${isCurrent ? 'current-plan' : ''}`} key={p.code}><span className="eyebrow">{p.publicCode || p.code}</span><h2>{p.name}</h2><strong className="plan-price">{money(p.monthly)}<small>/mo</small></strong><p>{limit(p, 'users', 'userLimit')} users · {limit(p, 'products', 'productLimit')} products · {limit(p, 'orders', 'orderLimit')} orders/month</p><ul>{p.features.map((f) => <li key={f}>{f}</li>)}</ul><button disabled={isCurrent} onClick={() => change(p)}>{isCurrent ? 'Current plan' : `Choose ${p.name}`}</button></article>; })}</div></div>;
}

function SubscriptionAdminPage({ mode, notice, setNotice }) {
  const { user, updateUser } = useAuth();
  const [live, setLive] = useState(null);
  const refresh = async () => { if (mode === 'api') { const next = await getApiResource('subscription'); setLive(next); if (user) updateUser({ ...user, subscription: next.subscription }); } };
  useEffect(() => { setLive(null); refresh().catch(() => {}); }, [mode]);
  const run = async (payload, message) => { try { if (mode === 'api') { const result = await createApiResource('subscription', payload); setNotice(result.checkout && !result.checkout.providerConfigured ? `${message} Configure the billing provider before collecting live payments.` : message); await refresh(); } else if (payload.action === 'change-plan' && user) { const selected = demoSubscription.plans.find((plan) => plan.code === payload.planCode || plan.publicCode === payload.planCode); if (selected) { const publicCode = selected.publicCode || selected.code; updateUser({ ...user, subscription: { ...(user.subscription || {}), code: publicCode, publicCode, plan: selected.code, name: selected.name, planName: selected.name, status: 'Active', periodEnd: null } }); setNotice(`Plan changed to ${selected.name}. Features are now available for this owner session.`); } else setNotice(message); } else setNotice(message); } catch (error) { setNotice(error.message); } };
  const change = (plan) => run({ action: 'change-plan', planCode: plan.code }, `Plan change to ${plan.name} requested.`);
  const demoCurrentCode = user?.subscription?.code || demoSubscription.subscription.publicCode;
  const demoPlan = demoSubscription.plans.find((plan) => plan.publicCode === demoCurrentCode || plan.code === demoCurrentCode) || demoSubscription.plans[0];
  const d = live || { ...demoSubscription, subscription: { ...demoSubscription.subscription, ...(user?.subscription || {}), code: demoCurrentCode, publicCode: demoCurrentCode, plan: demoPlan.code, name: demoPlan.name, planName: demoPlan.name } };
  const limits = d.limits || {};
  const current = d.subscription || {};
  const currentCode = current.publicCode || current.plan || current.code;
  const limit = (plan, key, legacy) => plan.limits?.[key] ?? plan[legacy] ?? '-';
  return <div>
    <div className="module-header"><div><span className="eyebrow">SaaS commercial layer</span><h1>Subscription billing</h1><p>Manage plan access, renewals, failed payments, invoices and cancellation for this company.</p></div><div className="button-row"><button onClick={() => run({ action: 'renew' }, 'Renewal checkout created.')}>Renew plan</button>{current.cancelAtPeriodEnd ? <button onClick={() => run({ action: 'resume' }, 'Subscription resumed.')}>Resume subscription</button> : <button className="button-secondary" onClick={() => run({ action: 'cancel' }, 'Cancellation scheduled for the period end.')}>Cancel at period end</button>}</div></div>
    <Notice text={notice}/>
    <div className="report-grid"><article><span>Current plan</span><strong>{current.planName || current.name}</strong><small>{current.status} - ends {current.periodEnd || 'No expiry'}{current.cancelAtPeriodEnd ? ' - cancellation scheduled' : ''}</small></article><article><span>Users</span><strong>{d.usage.users} / {limits.users || '-'}</strong><small>active team members</small></article><article><span>Products</span><strong>{d.usage.products ?? 0} / {limits.products || '-'}</strong><small>active catalogue SKUs</small></article><article><span>Orders this month</span><strong>{d.usage.orders ?? 0} / {limits.orders || '-'}</strong><small>monthly plan allowance</small></article></div>
    <div className="plan-grid">{d.plans.map((plan) => { const isCurrent = plan.publicCode === currentCode || plan.code === currentCode; return <article className={`panel ${isCurrent ? 'current-plan' : ''}`} key={plan.code}><span className="eyebrow">{plan.publicCode || plan.code}</span><h2>{plan.name}</h2><strong className="plan-price">{money(plan.monthly)}<small>/mo</small></strong><p>{limit(plan, 'users', 'userLimit')} users - {limit(plan, 'products', 'productLimit')} products - {limit(plan, 'orders', 'orderLimit')} orders/month</p><ul>{plan.features.map((feature) => <li key={feature}>{feature}</li>)}</ul><button disabled={isCurrent} onClick={() => change(plan)}>{isCurrent ? 'Current plan' : `Choose ${plan.name}`}</button></article>; })}</div>
    <div className="two-column-panels"><article className="panel module-panel"><div className="panel-head"><div><span>Billing documents</span><h3>Invoices</h3></div></div>{(d.invoices || []).length ? <div className="table-wrap"><table className="data-table"><thead><tr><th>Invoice</th><th>Amount</th><th>Due</th><th>Status</th></tr></thead><tbody>{d.invoices.map((invoice) => <tr key={invoice.invoiceNo}><td>{invoice.invoiceNo}</td><td>{money(invoice.amount)}</td><td>{invoice.dueDate}</td><td>{invoice.status}</td></tr>)}</tbody></table></div> : <p className="muted">Invoices will appear after the first checkout.</p>}</article><article className="panel module-panel"><div className="panel-head"><div><span>Payment attempts</span><h3>Checkout history</h3></div></div>{(d.payments || []).length ? <div className="table-wrap"><table className="data-table"><thead><tr><th>Provider</th><th>Amount</th><th>Status</th><th>Action</th></tr></thead><tbody>{d.payments.map((payment) => <tr key={payment.id}><td>{payment.provider}</td><td>{money(payment.amount)}</td><td>{payment.status}</td><td>{payment.status === 'Failed' ? <button className="table-action" onClick={() => run({ action: 'retry-payment', paymentId: payment.id }, 'Payment retry checkout created.')}>Retry</button> : payment.status === 'Pending' ? <small>Awaiting webhook</small> : <small>{payment.paymentId || 'Settled'}</small>}</td></tr>)}</tbody></table></div> : <p className="muted">No payment attempts yet.</p>}</article></div>
  </div>;
}

function ForecastingPage({ mode, notice, setNotice }) {
  const generate = async () => { try { if (mode === 'api') await createApiResource('forecasting', { horizon: 30 }); setNotice('30-day forecast regenerated from recent order demand.'); } catch (e) { setNotice(e.message); } };
  return <div><div className="module-header"><div><span className="eyebrow">Demand planning</span><h1>Advanced forecasting</h1><p>Blend recent demand, trend, safety stock and current inventory into transparent purchase recommendations.</p></div><button onClick={generate}>Regenerate 30-day forecast</button></div><Notice text={notice}/><article className="panel module-panel"><div className="table-wrap"><table className="data-table module-table"><thead><tr><th>Product</th><th>Stock</th><th>Daily demand</th><th>Trend</th><th>30d forecast</th><th>Safety</th><th>Buy</th><th>Confidence</th></tr></thead><tbody>{demoForecasts.map((x) => <tr key={x.sku}><td><strong>{x.product}</strong><small>{x.sku}</small></td><td>{x.currentStock}</td><td>{x.avgDaily}</td><td>{x.trend > 0 ? '+' : ''}{x.trend}%</td><td>{Math.round(x.forecast)}</td><td>{x.safetyStock}</td><td><strong>{Math.round(x.recommendedPurchase)}</strong></td><td>{x.confidence}%</td></tr>)}</tbody></table></div></article></div>;
}

function AssistantPage({ mode }) {
  const [messages, setMessages] = useState(demoAssistant);
  const [busy, setBusy] = useState(false);
  const ask = async (e) => {
    e.preventDefault(); const input = e.currentTarget.elements.question; const question = input.value.trim(); if (!question) return;
    setMessages((m) => [...m, { role: 'user', content: question }]); input.value = ''; setBusy(true);
    try {
      let answer;
      if (mode === 'api') answer = (await createApiResource('assistant', { question })).answer;
      else { const q = question.toLowerCase(); answer = q.includes('overdue') ? 'Top overdue demo accounts: Sethi Hardware House ₹1,24,600; NCR Buildmart ₹76,750.' : q.includes('stock') || q.includes('reorder') ? 'Polycab 2.5mm Wire and GM 8 Module Plate are the highest stock-risk demo items.' : 'Month-to-date demo sales are ₹42,86,400. Ask about overdue customers, stock risk, collections or reorder needs.'; }
      setMessages((m) => [...m, { role: 'assistant', content: answer }]);
    } catch (e2) { setMessages((m) => [...m, { role: 'assistant', content: e2.message }]); }
    finally { setBusy(false); }
  };
  return <div><div className="module-header"><div><span className="eyebrow">Data-grounded assistant</span><h1>AI Business Assistant</h1><p>Ask operational questions in plain language. Answers use tenant-scoped ERP data and existing user permissions.</p></div></div><div className="assistant-shell panel"><div className="assistant-messages">{messages.map((m, i) => <div key={i} className={`assistant-msg ${m.role}`}><span>{m.role === 'assistant' ? 'Setu' : 'You'}</span><p>{m.content}</p></div>)}{busy && <div className="assistant-msg assistant"><span>Setu</span><p>Checking business data…</p></div>}</div><form className="assistant-compose" onSubmit={ask}><input name="question" placeholder="Which products may run out next week?"/><button disabled={busy}>Ask</button></form><div className="assistant-prompts">{['Show overdue customers', 'What are month-to-date sales?', 'Which products are low stock?', 'What should I reorder?'].map((x) => <span key={x}>{x}</span>)}</div></div></div>;
}

export default function GrowthModulePage({ module }) {
  const { mode } = useAuth();
  const [notice, setNotice] = useState('');
  if (module === 'delivery') return <LiveDeliveryPage/>;
  if (module === 'approvals') return <ApprovalPage mode={mode} notice={notice} setNotice={setNotice}/>;
  if (module === 'invoice-ocr') return <InvoiceOcrPage mode={mode} notice={notice} setNotice={setNotice}/>;
  if (module === 'accounting') return <AccountingPage mode={mode} notice={notice} setNotice={setNotice}/>;
  if (module === 'offline') return <OfflinePage mode={mode} notice={notice} setNotice={setNotice}/>;
  if (module === 'subscription') return <SubscriptionAdminPage mode={mode} notice={notice} setNotice={setNotice}/>;
  if (module === 'forecasting') return <AIForecastingPage/>;
  if (module === 'assistant') return <AssistantPage mode={mode}/>;
  return null;
}
