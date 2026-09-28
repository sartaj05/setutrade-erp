import { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { createApiResource, getApiResource } from '../services/api';

const money = (value) => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(Number(value || 0));
const demo = {
  summary: { openRisks: 2, held: 1, unmatched: 3, highValue: 1, duplicatePatterns: 1 },
  transactions: [
    { id: 1, reference: 'UPI-884219', customer: 'Metro Electricals', amount: 148000, method: 'UPI', date: '2026-09-28', status: 'Unmatched', riskStatus: 'Held', riskLevel: 'critical', riskScore: 85, reasons: ['Payment is held for manual review.', 'Large UPI payment requires confirmation.'] },
    { id: 2, reference: 'UTR-552104', customer: 'R.K. Trading Co.', amount: 58240, method: 'Bank', date: '2026-09-28', status: 'Partial', riskStatus: 'Open', riskLevel: 'warning', riskScore: 45, reasons: ['Similar customer payment was received recently.'] },
    { id: 3, reference: 'UPI-884201', customer: 'Ahuja Enterprises', amount: 24000, method: 'UPI', date: '2026-09-27', status: 'Matched', riskStatus: 'Cleared', riskLevel: 'clear', riskScore: 0, reasons: ['Risk review cleared this payment.'] },
  ],
};

function RiskStatus({ level }) {
  return <span className={`risk-badge risk-${level}`}>{level === 'critical' ? 'High risk' : level === 'warning' ? 'Review' : 'Clear'}</span>;
}

export default function PaymentRiskPage() {
  const { mode } = useAuth();
  const [data, setData] = useState(demo);
  const [notice, setNotice] = useState('');
  const [busy, setBusy] = useState(false);
  const [form, setForm] = useState({ reference: 'UPI-NEW-001', amount: '75000', method: 'UPI', deviceRisk: 'normal' });

  const load = async () => {
    if (mode !== 'api') { setData(demo); return; }
    try { setData(await getApiResource('payment-risk')); } catch (error) { setNotice(error.message); }
  };
  useEffect(() => { load(); }, [mode]);

  const evaluate = async (event) => {
    event.preventDefault(); setBusy(true);
    try {
      const result = mode === 'api' ? await createApiResource('payment-risk', { action: 'evaluate', ...form, amount: Number(form.amount) }) : { score: 40, level: 'warning', reasons: ['Demo risk review completed.'] };
      setNotice(`${form.reference}: ${result.level === 'clear' ? 'no risk signal detected' : `${result.level} review required`} (${result.score}/100).`);
    } catch (error) { setNotice(error.message); } finally { setBusy(false); }
  };

  const setRiskState = async (row, action) => {
    try {
      if (mode === 'api') await createApiResource('payment-risk', { action, transactionId: row.id });
      setNotice(`${row.reference} ${action === 'hold' ? 'placed on manual hold' : 'cleared after review'}.`); load();
    } catch (error) { setNotice(error.message); }
  };

  const summary = data.summary || demo.summary;
  return <div className="payment-risk-page">
    {notice && <div className="risk-notice"><span>{notice}</span><button onClick={() => setNotice('')}>×</button></div>}
    <div className="module-header"><div><span className="section-kicker">Financial protection</span><h1>Payment risk control</h1><p>Detect duplicate receipts, risky UPI activity, invoice mismatches and credit-limit breaches before money reaches the ledger.</p></div></div>
    <div className="risk-summary"><div><span>Open risks</span><strong>{summary.openRisks}</strong><small>needs investigation</small></div><div><span>Manual holds</span><strong>{summary.held}</strong><small>blocked from auto-clear</small></div><div><span>Unmatched</span><strong>{summary.unmatched}</strong><small>awaiting allocation</small></div><div><span>Duplicate patterns</span><strong>{summary.duplicatePatterns}</strong><small>same customer and amount</small></div></div>
    <div className="risk-workspace">
      <article className="panel risk-simulator"><div className="panel-head"><div><span>Pre-flight review</span><h3>Check a proposed payment</h3></div></div><form onSubmit={evaluate} className="risk-form"><label>Reference<input value={form.reference} onChange={e => setForm({ ...form, reference: e.target.value })} /></label><label>Amount<input type="number" min="1" value={form.amount} onChange={e => setForm({ ...form, amount: e.target.value })} /></label><label>Method<select value={form.method} onChange={e => setForm({ ...form, method: e.target.value })}><option>UPI</option><option>Bank</option><option>Cash</option></select></label><label>Device signal<select value={form.deviceRisk} onChange={e => setForm({ ...form, deviceRisk: e.target.value })}><option value="normal">Normal</option><option value="high">High risk</option><option value="blocked">Blocked</option></select></label><button disabled={busy}>{busy ? 'Checking…' : 'Evaluate risk'}</button></form></article>
      <article className="panel risk-guidance"><div className="panel-head"><div><span>Control policy</span><h3>Safe payment handling</h3></div></div><ul><li><strong>60+ score</strong><span>place payment on hold and require finance review</span></li><li><strong>25–59 score</strong><span>keep visible in the risk queue before reconciliation</span></li><li><strong>0–24 score</strong><span>continue normal invoice matching</span></li></ul></article>
    </div>
    <article className="panel module-panel risk-table-panel"><div className="panel-head"><div><span>Transaction watchlist</span><h3>Recent payment signals</h3></div><small>Risk decisions remain in the payment audit trail.</small></div><div className="table-wrap"><table className="data-table module-table"><thead><tr><th>Reference</th><th>Customer</th><th>Amount</th><th>Signal</th><th>Reasons</th><th>Action</th></tr></thead><tbody>{(data.transactions || []).map(row => <tr key={row.id}><td><strong>{row.reference}</strong><small>{row.method} · {row.date}</small></td><td>{row.customer}</td><td>{money(row.amount)}</td><td><RiskStatus level={row.riskLevel}/><small>{row.riskScore}/100 · {row.riskStatus}</small></td><td>{(row.reasons || []).join(' ')}</td><td>{row.riskStatus === 'Held' ? <button className="table-action" onClick={() => setRiskState(row, 'release')}>Clear review</button> : row.riskStatus === 'Cleared' ? 'Cleared' : <button className="table-action danger-action" onClick={() => setRiskState(row, 'hold')}>Hold payment</button>}</td></tr>)}</tbody></table></div></article>
  </div>;
}
