import { useEffect, useState } from 'react';
import { apiRequest } from '../services/api';

const money = (value) => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(Number(value || 0));

export default function BankStatementImportCard({ mode }) {
  const [data, setData] = useState({ imports: [], lines: [] });
  const [notice, setNotice] = useState('');
  const [busy, setBusy] = useState(false);

  const load = async () => {
    if (mode !== 'api') return;
    try { setData(await apiRequest('/payments/statement-import/')); } catch (error) { setNotice(error.message); }
  };

  useEffect(() => { load(); }, [mode]);

  const upload = async (event) => {
    const file = event.target.files?.[0];
    event.target.value = '';
    if (!file || mode !== 'api') return;
    setBusy(true);
    try {
      const form = new FormData();
      form.append('file', file);
      const result = await apiRequest('/payments/statement-import/', { method: 'POST', body: form });
      setNotice(`Imported ${result.import.rows} row(s): ${result.import.imported} new, ${result.import.duplicates} duplicate, ${result.import.errors} error(s).`);
      await load();
    } catch (error) { setNotice(error.message); } finally { setBusy(false); }
  };

  const autoMatch = async () => {
    if (mode !== 'api') return setNotice('Auto-match is available with the live Django API.');
    setBusy(true);
    try { const result = await apiRequest('/payments/statement-import/', { method: 'POST', body: JSON.stringify({ action: 'auto-match' }) }); setNotice(`${result.matched} receipt(s) matched to open invoices.`); await load(); } catch (error) { setNotice(error.message); } finally { setBusy(false); }
  };

  return <article className="panel module-panel"><div className="panel-head"><div><span>Bank feed</span><h3>Statement import & review</h3></div><div className="row-actions"><button className="secondary-btn" onClick={autoMatch} disabled={busy}>Auto-match receipts</button><label className="secondary-btn csv-button">{busy ? 'Importing…' : 'Import CSV'}<input type="file" accept=".csv,text/csv" hidden disabled={busy || mode !== 'api'} onChange={upload} /></label></div></div><p className="muted">Credit rows with a matching customer become duplicate-safe bank transactions. Auto-match allocates them to the oldest open invoices; unmatched credits stay visible for review.</p>{notice && <div className="inline-notice">{notice}</div>}<div className="table-wrap"><table className="data-table module-table"><thead><tr><th>Date</th><th>Reference</th><th>Description</th><th>Amount</th><th>Customer</th><th>Status</th></tr></thead><tbody>{(data.lines || []).map((line) => <tr key={line.id}><td>{line.date}</td><td><strong>{line.reference || '—'}</strong></td><td>{line.description || '—'}</td><td className={line.direction === 'Debit' ? 'negative' : 'positive'}>{line.direction === 'Debit' ? '-' : '+'}{money(line.amount)}</td><td>{line.customer || 'Needs matching'}</td><td>{line.status}</td></tr>)}{!data.lines?.length && <tr><td colSpan="6" className="muted">No bank statement rows imported yet.</td></tr>}</tbody></table></div></article>;
}
