import { useState } from 'react';
import { downloadCsv, importCsv } from '../services/api';
import { useAuth } from '../context/AuthContext';

const resources = [
  ['products', 'Products', 'SKU, pricing, GST and reorder settings'], ['customers', 'Customers', 'Dealer accounts, GSTIN and credit limits'], ['suppliers', 'Suppliers', 'Supplier master and contact details'],
  ['opening-stock', 'Opening stock', 'Warehouse balances and reserved quantity'], ['ledger', 'Customer ledger', 'Invoice, payment and ageing history'], ['invoices', 'Invoices', 'Invoice headers linked to existing orders'],
];

export default function DataExchangePage() {
  const { mode, user } = useAuth(); const [notice, setNotice] = useState(''); const [busy, setBusy] = useState('');
  const canImport = ['OWNER', 'MANAGER'].includes(user.role);
  const upload = async (resource, event) => { const file = event.target.files?.[0]; if (!file) return; setBusy(resource); try { if (mode !== 'api') setNotice('Demo mode: connect Django to import client data.'); else { const result = await importCsv(resource, file); setNotice(`${result.rows} ${resource} row(s) processed: ${result.created} created, ${result.updated} updated.`); } } catch (err) { setNotice(err.message); } finally { setBusy(''); event.target.value = ''; } };
  const exportIt = async (resource) => { try { if (mode !== 'api') return setNotice('Demo mode: exports are available with the live Django API.'); await downloadCsv(resource); setNotice(`${resource} export downloaded.`); } catch (err) { setNotice(err.message); } };
  return <div className="exchange-page"><div className="module-header"><div><span className="section-kicker">Client data operations</span><h1>Import & export center</h1><p>Move approved master data into SetuStock and give the client controlled, auditable exports for finance and operations.</p></div><span className="feature-badge">CSV + XLSX tools</span></div>{notice && <div className="inline-notice">{notice}</div>}<div className="exchange-grid">{resources.map(([resource, title, description]) => <article className="panel exchange-card" key={resource}><div><span>{resource === 'opening-stock' ? 'Inventory' : resource === 'ledger' || resource === 'invoices' ? 'Finance' : 'Master data'}</span><h3>{title}</h3><p>{description}</p></div><div className="row-actions"><button className="secondary-btn" onClick={() => exportIt(resource)}>Export CSV</button>{canImport && resource !== 'ledger' && <label className="secondary-btn csv-button">{busy === resource ? 'Importing…' : 'Import CSV / XLSX'}<input type="file" accept=".csv,.xlsx,text/csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" hidden onChange={(event) => upload(resource, event)} /></label>}</div></article>)}</div><div className="exchange-note"><strong>Import rules</strong><span>Products, customers and suppliers upsert by their code. Opening stock matches SKU + warehouse code. Invoice imports require an existing order number, preventing unlinked accounting records.</span></div></div>;
}
