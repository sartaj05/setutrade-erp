import { useMemo, useState } from 'react';
import { demoCustomers, demoDashboard, demoInvoices, demoProducts } from '../data/demoData';
import { useApiData } from '../services/useApiData';
import EnhancedModulePage from './EnhancedModulePage';

const money = (value) => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(value);

function Toolbar({ title, subtitle, action = 'Add new', search, setSearch }) {
  return (
    <div className="module-header">
      <div><span className="section-kicker">Operations</span><h1>{title}</h1><p>{subtitle}</p></div>
      <div className="module-actions"><input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search…" /><button>{action}</button></div>
    </div>
  );
}

function Products({ inventoryOnly = false }) {
  const [search, setSearch] = useState('');
  const { data: products } = useApiData('products', demoProducts, 'products');
  const rows = useMemo(() => products.filter((p) => `${p.name} ${p.sku} ${p.category}`.toLowerCase().includes(search.toLowerCase())), [search, products]);
  return (
    <div>
      <Toolbar title={inventoryOnly ? 'Inventory' : 'Products'} subtitle={inventoryOnly ? 'Know what is available, low and due for replenishment.' : 'Your sellable catalogue, pricing and stock position.'} action={inventoryOnly ? 'Stock adjustment' : 'Add product'} search={search} setSearch={setSearch} />
      <div className="module-summary">
        <div><span>Total SKUs</span><strong>248</strong><small>212 active</small></div>
        <div><span>Low stock</span><strong>8</strong><small>3 critical</small></div>
        <div><span>Stock value</span><strong>₹31.84L</strong><small>purchase cost</small></div>
      </div>
      <article className="panel module-panel">
        <div className="table-wrap"><table className="data-table module-table"><thead><tr><th>Product / SKU</th><th>Category</th><th>Available</th><th>{inventoryOnly ? 'Reorder level' : 'Sell price'}</th><th>Location</th><th>State</th></tr></thead><tbody>
          {rows.map((p) => { const low = p.stock <= p.reorder; return <tr key={p.sku}><td><strong>{p.name}</strong><small>{p.sku}</small></td><td>{p.category}</td><td><strong>{p.stock} {p.unit}</strong></td><td>{inventoryOnly ? `${p.reorder} ${p.unit}` : money(p.sell)}</td><td>{p.location}</td><td><span className={`status-pill ${low ? 'processing' : 'ready'}`}>{low ? 'Reorder' : 'Healthy'}</span></td></tr>; })}
        </tbody></table></div>
      </article>
    </div>
  );
}

function Customers() {
  const [search, setSearch] = useState('');
  const { data: customers } = useApiData('customers', demoCustomers, 'customers');
  const rows = useMemo(() => customers.filter((c) => `${c.name} ${c.city} ${c.phone}`.toLowerCase().includes(search.toLowerCase())), [search, customers]);
  return (
    <div>
      <Toolbar title="Customers & credit" subtitle="Credit limits, outstanding balances and collection follow-ups in one ledger view." action="Add customer" search={search} setSearch={setSearch} />
      <div className="module-summary"><div><span>Active customers</span><strong>86</strong><small>18 on credit</small></div><div><span>Total receivable</span><strong>₹4.72L</strong><small>5 overdue</small></div><div><span>Due this week</span><strong>₹1.38L</strong><small>11 invoices</small></div></div>
      <article className="panel module-panel"><div className="table-wrap"><table className="data-table module-table"><thead><tr><th>Customer</th><th>City</th><th>Outstanding</th><th>Credit limit</th><th>Due</th><th>Action</th></tr></thead><tbody>
        {rows.map((c) => <tr key={c.id}><td><strong>{c.name}</strong><small>{c.phone}</small></td><td>{c.city}</td><td><strong>{money(c.outstanding)}</strong><small><span className={`credit-state ${c.status.toLowerCase()}`}>{c.status}</span></small></td><td>{money(c.limit)}</td><td>{c.due}</td><td><a className="whatsapp-link" href={`https://wa.me/91${c.phone}?text=${encodeURIComponent(`Hello ${c.name}, this is a demo payment follow-up from SetuStock.`)}`} target="_blank" rel="noreferrer">WhatsApp ↗</a></td></tr>)}
      </tbody></table></div></article>
    </div>
  );
}

function Orders() {
  const [search, setSearch] = useState('');
  const { data: orders } = useApiData('orders', demoDashboard.recentOrders, 'orders');
  const rows = useMemo(() => orders.filter((o) => `${o.id} ${o.customer} ${o.status}`.toLowerCase().includes(search.toLowerCase())), [search, orders]);
  return (
    <div>
      <Toolbar title="B2B orders" subtitle="Move counter, phone and WhatsApp orders through one dispatch queue." action="Create order" search={search} setSearch={setSearch} />
      <div className="order-board"><div><span>01</span><strong>New order</strong><small>Capture customer + items</small></div><i>→</i><div><span>02</span><strong>Reserve stock</strong><small>Check quantity availability</small></div><i>→</i><div><span>03</span><strong>Pick & pack</strong><small>Warehouse execution</small></div><i>→</i><div><span>04</span><strong>Dispatch</strong><small>Invoice + delivery</small></div></div>
      <article className="panel module-panel"><div className="table-wrap"><table className="data-table module-table"><thead><tr><th>Order</th><th>Customer</th><th>Total</th><th>Payment</th><th>Status</th><th>Action</th></tr></thead><tbody>
        {rows.map((order) => <tr key={order.id}><td><strong>{order.id}</strong><small>{order.date}</small></td><td>{order.customer}</td><td>{money(order.total)}</td><td><span className={`text-status ${order.payment.toLowerCase()}`}>{order.payment}</span></td><td><span className={`status-pill ${order.status.toLowerCase()}`}>{order.status}</span></td><td><button className="table-action">Open</button></td></tr>)}
      </tbody></table></div></article>
    </div>
  );
}


function Invoices() {
  const [search, setSearch] = useState('');
  const { data: invoices } = useApiData('invoices', demoInvoices, 'invoices');
  const rows = useMemo(() => invoices.filter((i) => `${i.id} ${i.customer} ${i.order} ${i.gstin}`.toLowerCase().includes(search.toLowerCase())), [search, invoices]);
  return (
    <div>
      <Toolbar title="GST invoices" subtitle="GST-ready invoice records linked to customer orders and payment status." action="Create invoice" search={search} setSearch={setSearch} />
      <div className="module-summary"><div><span>September invoices</span><strong>42</strong><small>₹18.7L billed</small></div><div><span>GST collected</span><strong>₹2.41L</strong><small>demo tax total</small></div><div><span>Unpaid invoices</span><strong>11</strong><small>₹3.18L due</small></div></div>
      <article className="panel module-panel"><div className="table-wrap"><table className="data-table module-table"><thead><tr><th>Invoice</th><th>Customer / GSTIN</th><th>Order</th><th>Taxable</th><th>GST</th><th>Total</th><th>Status</th></tr></thead><tbody>
        {rows.map((i) => <tr key={i.id}><td><strong>{i.id}</strong><small>{i.date}</small></td><td><strong>{i.customer}</strong><small>{i.gstin}</small></td><td>{i.order}</td><td>{money(i.taxable)}</td><td>{money(i.tax)}</td><td><strong>{money(i.total)}</strong></td><td><span className={`text-status ${i.status.toLowerCase()}`}>{i.status}</span></td></tr>)}
      </tbody></table></div></article>
    </div>
  );
}

function SimpleModule({ module }) {
  const [search, setSearch] = useState('');
  const content = {
    quotations: ['Quotations', 'Turn customer enquiries into priced B2B offers and later convert approved quotes to orders.', 'New quotation'],
    payments: ['Payments & collections', 'Track incoming payments, ageing receivables and customer collection follow-ups.', 'Record payment'],
    reports: ['Reports', 'A compact operating view of sales, inventory movement, margins and receivables.', 'Export CSV'],
    team: ['Team & roles', 'Control who can see financial, sales and warehouse information.', 'Invite user'],
    settings: ['Business settings', 'Manage company profile, GST fields, invoice defaults and demo integration settings.', 'Save settings'],
  }[module];
  return (
    <div>
      <Toolbar title={content[0]} subtitle={content[1]} action={content[2]} search={search} setSearch={setSearch} />
      <div className="coming-grid">
        {module === 'payments' && <><article><span>Outstanding</span><strong>₹4.72L</strong><p>Across 18 credit customers.</p></article><article><span>Overdue</span><strong>₹1.63L</strong><p>5 accounts need follow-up.</p></article><article><span>Collected this month</span><strong>₹12.8L</strong><p>73% via bank / UPI.</p></article></>}
        {module === 'reports' && <><article><span>Gross sales</span><strong>₹42.86L</strong><p>September running total.</p></article><article><span>Estimated margin</span><strong>14.8%</strong><p>Based on demo purchase costs.</p></article><article><span>Inventory turns</span><strong>5.2×</strong><p>Annualised demo indicator.</p></article></>}
        {!['payments','reports'].includes(module) && <article className="wide-coming"><span>Module scaffold ready</span><strong>{content[0]}</strong><p>This page is permission-aware and ready for its Django endpoints in the next phase. The demo keeps the route visible so sales demos do not hit a dead end.</p></article>}
      </div>
    </div>
  );
}

export default function ModulePage({ module }) {
  if (['purchases'].includes(module)) return <EnhancedModulePage module={module} />;
  if (module === 'products') return <Products />;
  if (module === 'inventory') return <Products inventoryOnly />;
  if (module === 'customers') return <Customers />;
  if (module === 'orders') return <Orders />;
  if (module === 'invoices') return <Invoices />;
  return <SimpleModule module={module} />;
}
