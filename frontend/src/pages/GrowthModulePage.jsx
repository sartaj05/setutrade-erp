import { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { createApiResource } from '../services/api';
import { queueOfflineEvent, listOfflineEvents, removeOfflineEvents } from '../services/offlineQueue';
import {
  demoDelivery, demoApprovals, demoCaptures, demoAccounting, demoOffline,
  demoSubscription, demoForecasts, demoAssistant,
} from '../data/growthData';

const money = (n) => `₹${Number(n || 0).toLocaleString('en-IN')}`;
const Notice = ({ text }) => text ? <div className="inline-notice">{text}</div> : null;

function DeliveryPage({ mode, notice, setNotice }) {
  const deliver = async (stop) => {
    try {
      if (mode === 'api') await createApiResource('delivery', { action: 'deliver', stopId: stop.id, otpVerified: true, receiverName: 'Demo receiver' });
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

function ApprovalPage({ mode, notice, setNotice }) {
  const decide = async (row, action) => {
    try { if (mode === 'api') await createApiResource('approvals', { id: row.id, action }); setNotice(`${action === 'approve' ? 'Approved' : 'Rejected'} ${row.requestNo}.`); }
    catch (e) { setNotice(e.message); }
  };
  return <div><div className="module-header"><div><span className="eyebrow">Exception control</span><h1>Approval workflows</h1><p>Route high discounts, credit overrides, returns and sensitive transactions to the correct approver.</p></div><button onClick={() => setNotice('Policy editor is company-scoped and API-ready.')}>Manage policies</button></div><Notice text={notice}/><div className="report-grid">{demoApprovals.policies.map((p) => <article key={p.key}><span>{p.label}</span><strong>{p.approverRole}</strong><small>{p.active ? 'Policy active' : 'Disabled'}</small></article>)}</div><article className="panel module-panel"><div className="table-wrap"><table className="data-table module-table"><thead><tr><th>Request</th><th>Reason</th><th>Requested by</th><th>Amount</th><th>Status</th><th>Decision</th></tr></thead><tbody>{demoApprovals.requests.map((r) => <tr key={r.id}><td>{r.requestNo}</td><td><strong>{r.title}</strong><small>{r.entity}</small></td><td>{r.requestedBy}</td><td>{money(r.amount)}</td><td>{r.status}</td><td>{r.status === 'Pending' ? <div className="row-actions"><button className="table-action" onClick={() => decide(r, 'approve')}>Approve</button><button className="table-action" onClick={() => decide(r, 'reject')}>Reject</button></div> : '—'}</td></tr>)}</tbody></table></div></article></div>;
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
  return <div><div className="module-header"><div><span className="eyebrow">Books bridge</span><h1>Accounting integration</h1><p>Prepare sales, purchase, receipt and payment vouchers for Tally, Zoho Books or accountant-friendly CSV export.</p></div><button onClick={run}>Generate export</button></div><Notice text={notice}/><div className="report-grid"><article><span>Connector</span><strong>Tally / CSV</strong><small>credential-free demo mode</small></article><article><span>Voucher types</span><strong>4</strong><small>sales, purchase, receipt, payment</small></article><article><span>Last pack</span><strong>318</strong><small>vouchers</small></article></div><article className="panel module-panel"><div className="table-wrap"><table className="data-table module-table"><thead><tr><th>Export</th><th>Provider</th><th>Period</th><th>Vouchers</th><th>Status</th></tr></thead><tbody>{jobs.map((j) => <tr key={j.id}><td>{j.exportNo}</td><td>{j.provider}</td><td>{j.from} → {j.to}</td><td>{j.voucherCount}</td><td>{j.status}</td></tr>)}</tbody></table></div></article></div>;
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
  const change = async (plan) => { try { if (mode === 'api') await createApiResource('subscription', { action: 'change-plan', planCode: plan.code }); setNotice(`Plan changed to ${plan.name}. Billing invoice created.`); } catch (e) { setNotice(e.message); } };
  const d = demoSubscription;
  return <div><div className="module-header"><div><span className="eyebrow">SaaS commercial layer</span><h1>Subscription billing</h1><p>Control trials, plan limits, recurring billing state and SaaS invoices per client company.</p></div></div><Notice text={notice}/><div className="report-grid"><article><span>Current plan</span><strong>{d.subscription.planName}</strong><small>{d.subscription.status} · ends {d.subscription.periodEnd}</small></article><article><span>Users</span><strong>{d.usage.users} / 10</strong><small>plan usage</small></article><article><span>Warehouses</span><strong>{d.usage.warehouses} / 5</strong><small>plan usage</small></article></div><div className="plan-grid">{d.plans.map((p) => <article className="panel" key={p.code}><span className="eyebrow">{p.code}</span><h2>{p.name}</h2><strong className="plan-price">{money(p.monthly)}<small>/mo</small></strong><ul>{p.features.map((f) => <li key={f}>{f}</li>)}</ul><button onClick={() => change(p)}>Choose {p.name}</button></article>)}</div></div>;
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
  if (module === 'delivery') return <DeliveryPage mode={mode} notice={notice} setNotice={setNotice}/>;
  if (module === 'approvals') return <ApprovalPage mode={mode} notice={notice} setNotice={setNotice}/>;
  if (module === 'invoice-ocr') return <InvoiceOcrPage mode={mode} notice={notice} setNotice={setNotice}/>;
  if (module === 'accounting') return <AccountingPage mode={mode} notice={notice} setNotice={setNotice}/>;
  if (module === 'offline') return <OfflinePage mode={mode} notice={notice} setNotice={setNotice}/>;
  if (module === 'subscription') return <SubscriptionPage mode={mode} notice={notice} setNotice={setNotice}/>;
  if (module === 'forecasting') return <ForecastingPage mode={mode} notice={notice} setNotice={setNotice}/>;
  if (module === 'assistant') return <AssistantPage mode={mode}/>;
  return null;
}
