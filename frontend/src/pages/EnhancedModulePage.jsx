import { useMemo, useState } from 'react';
import { useApiData } from '../services/useApiData';
import { demoPurchases } from '../data/featureData';

const money = (value) => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(value);

function FeatureHeader({ eyebrow, title, subtitle, action, search, setSearch }) {
  return <div className="module-header"><div><span className="section-kicker">{eyebrow}</span><h1>{title}</h1><p>{subtitle}</p></div><div className="module-actions"><input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search…" /><button>{action}</button></div></div>;
}

function Kpis({ items }) {
  return <div className="module-summary">{items.map((item) => <div key={item.label}><span>{item.label}</span><strong>{item.value}</strong><small>{item.note}</small></div>)}</div>;
}

function Badge({ children }) {
  const key = String(children).toLowerCase().replace(/\s+/g, '-');
  return <span className={`feature-badge ${key}`}>{children}</span>;
}

function PurchasesPage() {
  const [search, setSearch] = useState('');
  const { data: purchases } = useApiData('purchases', demoPurchases, 'purchases');
  const rows = useMemo(() => purchases.filter((x) => `${x.id} ${x.supplier} ${x.status}`.toLowerCase().includes(search.toLowerCase())), [purchases, search]);
  return <div><FeatureHeader eyebrow="Procurement" title="Suppliers & purchases" subtitle="Create purchase orders, track expected stock and receive goods without losing the paper trail." action="New purchase order" search={search} setSearch={setSearch} />
    <Kpis items={[{ label: 'Open POs', value: '11', note: '4 due this week' }, { label: 'Incoming stock', value: '₹6.42L', note: 'across 8 suppliers' }, { label: 'Supplier payable', value: '₹3.37L', note: 'demo outstanding' }]} />
    <div className="feature-flow"><span>Purchase order</span><i>→</i><span>Supplier confirmation</span><i>→</i><span>Goods receipt</span><i>→</i><span>Stock updated</span></div>
    <article className="panel module-panel"><div className="table-wrap"><table className="data-table module-table"><thead><tr><th>Purchase order</th><th>Supplier</th><th>Items</th><th>Total</th><th>Expected</th><th>Status</th></tr></thead><tbody>{rows.map((row) => <tr key={row.id}><td><strong>{row.id}</strong><small>{row.date}</small></td><td>{row.supplier}</td><td>{row.items}</td><td><strong>{money(row.total)}</strong></td><td>{row.expected}</td><td><Badge>{row.status}</Badge></td></tr>)}</tbody></table></div></article>
  </div>;
}

export default function EnhancedModulePage({ module }) {
  if (module === 'purchases') return <PurchasesPage />;
  return null;
}
