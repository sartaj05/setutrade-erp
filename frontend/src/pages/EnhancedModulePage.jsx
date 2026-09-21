import { useMemo, useState } from 'react';
import { useApiData } from '../services/useApiData';
import { demoPurchases, demoLedger, demoWarehouses, demoBarcodes, demoWhatsAppDrafts, demoTax, demoPricing } from '../data/featureData';

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

function LedgerPage() {
  const [search, setSearch] = useState('');
  const { data: ledger } = useApiData('ledger', demoLedger, 'ledger');
  const rows = useMemo(() => ledger.filter((x) => `${x.customer} ${x.reference} ${x.bucket}`.toLowerCase().includes(search.toLowerCase())), [ledger, search]);
  return <div><FeatureHeader eyebrow="Collections" title="Customer credit ledger" subtitle="See every invoice, payment and overdue balance with ageing buckets built for collection follow-ups." action="Record payment" search={search} setSearch={setSearch} />
    <Kpis items={[{ label: 'Receivable', value: '₹4.72L', note: '18 credit customers' }, { label: 'Overdue', value: '₹1.63L', note: '5 accounts need action' }, { label: 'Due next 7 days', value: '₹1.38L', note: '11 invoice references' }]} />
    <div className="ageing-strip"><div><span>Current</span><strong>₹3.09L</strong></div><div><span>1-30 days</span><strong>₹1.63L</strong></div><div><span>31-60</span><strong>₹0</strong></div><div><span>60+</span><strong>₹0</strong></div></div>
    <article className="panel module-panel"><div className="table-wrap"><table className="data-table module-table"><thead><tr><th>Customer</th><th>Reference</th><th>Type</th><th>Amount</th><th>Due</th><th>Ageing</th></tr></thead><tbody>{rows.map((row) => <tr key={`${row.customerId}-${row.reference}`}><td><strong>{row.customer}</strong><small>{row.customerId}</small></td><td>{row.reference}</td><td>{row.type}</td><td><strong>{money(row.amount)}</strong></td><td>{row.due}</td><td><Badge>{row.bucket}</Badge></td></tr>)}</tbody></table></div></article>
  </div>;
}

function WarehousesPage() {
  const [search, setSearch] = useState('');
  const { data } = useApiData('warehouses', demoWarehouses);
  const locations = data.warehouses || demoWarehouses.warehouses;
  const transfers = (data.transfers || demoWarehouses.transfers).filter((x) => `${x.id} ${x.from} ${x.to}`.toLowerCase().includes(search.toLowerCase()));
  return <div><FeatureHeader eyebrow="Inventory network" title="Multi-warehouse control" subtitle="See available and reserved stock by location, then move inventory with a traceable transfer workflow." action="New transfer" search={search} setSearch={setSearch} />
    <div className="warehouse-grid">{locations.map((w) => <article className="warehouse-card" key={w.id}><span>{w.id}</span><strong>{w.name}</strong><small>{w.city}</small><div><b>{w.stock}</b> units <em>{w.reserved} reserved</em></div></article>)}</div>
    <article className="panel module-panel"><div className="panel-head"><div><span>Movement</span><h3>Recent stock transfers</h3></div></div><div className="table-wrap"><table className="data-table module-table"><thead><tr><th>Transfer</th><th>From</th><th>To</th><th>Units</th><th>Date</th><th>Status</th></tr></thead><tbody>{transfers.map((row) => <tr key={row.id}><td><strong>{row.id}</strong></td><td>{row.from}</td><td>{row.to}</td><td>{row.units}</td><td>{row.date}</td><td><Badge>{row.status}</Badge></td></tr>)}</tbody></table></div></article>
  </div>;
}

function BarcodePage() {
  const { data: barcodes } = useApiData('barcode', demoBarcodes, 'barcodes');
  const [code, setCode] = useState('');
  const [last, setLast] = useState(barcodes[0] || demoBarcodes[0]);
  const scan = () => { const match = barcodes.find((p) => p.barcode === code.trim() || p.sku.toLowerCase() === code.trim().toLowerCase()); setLast(match || null); };
  return <div><FeatureHeader eyebrow="Warehouse speed" title="Barcode & QR scanning" subtitle="Use a USB scanner or phone-friendly input to identify stock, prepare labels and reduce manual SKU mistakes." action="Print labels" search={code} setSearch={setCode} />
    <div className="scanner-layout"><article className="scanner-box"><span className="section-kicker">Live scan</span><h3>Scan product barcode</h3><p>Place the cursor in the scanner field. Most USB scanners behave like a keyboard and work immediately.</p><div className="scan-entry"><input autoFocus value={code} onChange={(e)=>setCode(e.target.value)} onKeyDown={(e)=>{if(e.key==='Enter') scan();}} placeholder="Barcode or SKU"/><button onClick={scan}>Scan</button></div><small>Demo barcode: 8901762048129</small></article>
      <article className="scan-result">{last ? <><span>Matched product</span><strong>{last.name}</strong><small>{last.sku} · {last.location}</small><div className="barcode-visual">{last.barcode}</div><p><b>{last.stock}</b> {last.unit} currently available</p></> : <><span>No match</span><strong>Barcode not found</strong><p>Try a demo barcode or an existing SKU.</p></>}</article></div>
    <article className="panel module-panel"><div className="table-wrap"><table className="data-table module-table"><thead><tr><th>Product</th><th>Barcode</th><th>Location</th><th>Stock</th><th>Label</th></tr></thead><tbody>{barcodes.map((row)=><tr key={row.sku}><td><strong>{row.name}</strong><small>{row.sku}</small></td><td className="mono-cell">{row.barcode}</td><td>{row.location}</td><td>{row.stock} {row.unit}</td><td><button className="table-action">Print</button></td></tr>)}</tbody></table></div></article>
  </div>;
}

function WhatsAppPage() {
  const { data: drafts } = useApiData('whatsapp', demoWhatsAppDrafts, 'whatsapp');
  const [message, setMessage] = useState('Need 20 Anchor 32A MCB and 10 Havells 12W LED bulbs');
  const [draft, setDraft] = useState(demoWhatsAppDrafts[0]);
  const parseDemo = () => {
    const lower = message.toLowerCase(); const items = [];
    demoBarcodes.forEach((p) => { if (lower.includes(p.sku.toLowerCase()) || lower.includes(p.name.toLowerCase().split(' ')[0].toLowerCase())) { const match = message.match(/(\d+)\s+(?:x\s+)?(?:[A-Za-z])/); const quantity = match ? Number(match[1]) : 1; items.push({ ...p, quantity, price: p.sku === 'AN-MCB-32' ? 495 : p.sku === 'HA-LED-12' ? 145 : 2040, available: p.stock }); } });
    setDraft({ id: 'WA-DEMO-NEW', customer: 'R.K. Trading Co.', message, status: 'Draft', items, total: items.reduce((sum,x)=>sum+x.quantity*x.price,0) });
  };
  return <div><FeatureHeader eyebrow="Conversational commerce" title="WhatsApp B2B ordering" subtitle="Turn customer chat messages into structured draft orders, then check stock and move them into quotation or confirmation." action="Connect WhatsApp" search={''} setSearch={()=>{}} />
    <div className="whatsapp-layout"><article className="chat-card"><div className="chat-head"><span>R.K. Trading Co.</span><Badge>Online</Badge></div><div className="chat-bubble">{message}</div><textarea value={message} onChange={(e)=>setMessage(e.target.value)} /><button onClick={parseDemo}>Parse into order</button></article>
      <article className="draft-card"><span className="section-kicker">Draft order</span><h3>{draft?.id}</h3><p>{draft?.customer}</p><div className="draft-items">{(draft?.items || []).map((item)=><div key={item.sku}><span>{item.name}<small>{item.sku} · stock {item.available}</small></span><strong>{item.quantity} × {money(item.price)}</strong></div>)}</div><div className="draft-total"><span>Estimated total</span><strong>{money(draft?.total || 0)}</strong></div><div className="draft-actions"><button>Check stock</button><button>Create quotation</button></div></article></div>
    <article className="panel module-panel"><div className="panel-head"><div><span>Recent</span><h3>WhatsApp order drafts</h3></div></div><div className="table-wrap"><table className="data-table module-table"><thead><tr><th>Draft</th><th>Customer</th><th>Message</th><th>Total</th><th>Status</th></tr></thead><tbody>{drafts.map((row)=><tr key={row.id}><td><strong>{row.id}</strong></td><td>{row.customer}</td><td>{String(row.message).slice(0,55)}{String(row.message).length>55?'…':''}</td><td>{money(row.total)}</td><td><Badge>{row.status}</Badge></td></tr>)}</tbody></table></div></article>
  </div>;
}

function TaxPage() {
  const [search, setSearch] = useState('');
  const { data } = useApiData('tax', { tax: demoTax, demoPricing }, 'tax');
  const tax = data?.invoices ? data : demoTax;
  const rows = tax.invoices.filter((x)=>`${x.id} ${x.customer} ${x.gstin}`.toLowerCase().includes(search.toLowerCase()));
  return <div><FeatureHeader eyebrow="Compliance" title="GST, credit notes & e-invoice readiness" subtitle="Keep tax fields explicit: HSN/GST rates, place of supply, CGST/SGST/IGST, credit notes and provider-ready e-invoice status." action="Create credit note" search={search} setSearch={setSearch} />
    <Kpis items={[{label:'Taxable this month',value:'₹15.89L',note:'demo invoice base'},{label:'GST collected',value:'₹2.86L',note:'CGST + SGST + IGST'},{label:'E-invoice queue',value:'7',note:'provider connection required'}]} />
    <div className="tax-callout"><div><span>E-invoice connector</span><strong>Provider-ready, disabled in demo</strong><small>{tax.integration?.message}</small></div><Badge>Configurable</Badge></div>
    <article className="panel module-panel"><div className="table-wrap"><table className="data-table module-table"><thead><tr><th>Invoice</th><th>Customer / GSTIN</th><th>Taxable</th><th>CGST + SGST</th><th>IGST</th><th>Supply</th><th>E-invoice</th></tr></thead><tbody>{rows.map((i)=><tr key={i.id}><td><strong>{i.id}</strong></td><td><strong>{i.customer}</strong><small>{i.gstin}</small></td><td>{money(i.taxable)}</td><td>{money(i.cgst+i.sgst)}</td><td>{money(i.igst)}</td><td><strong>{i.supplyType}</strong><small>{i.placeOfSupply}</small></td><td><Badge>{i.einvoice}</Badge></td></tr>)}</tbody></table></div></article>
    <div className="feature-cards tax-notes">{tax.notes.map((n)=><article className="feature-card-compact" key={n.id}><span>{n.type}</span><strong>{n.id}</strong><small>{n.customer} · {n.invoice}</small><p>{n.reason}</p><b>{money(n.total)}</b></article>)}</div>
  </div>;
}

function PricingPage() {
  const [search, setSearch] = useState('');
  const { data: lists } = useApiData('pricing', demoPricing, 'pricing');
  const rules = lists.flatMap((pl)=>pl.rules.map((r)=>({...r,list:pl.name,customer:pl.customer}))).filter((x)=>`${x.product} ${x.sku} ${x.list} ${x.customer}`.toLowerCase().includes(search.toLowerCase()));
  const [qty,setQty]=useState(12);
  const sampleRules=demoPricing[0].rules.filter((x)=>x.sku==='AN-MCB-32').sort((a,b)=>a.minQty-b.minQty);
  const applied=[...sampleRules].reverse().find((x)=>qty>=x.minQty)||sampleRules[0];
  return <div><FeatureHeader eyebrow="Commercial controls" title="Customer pricing & schemes" subtitle="Define dealer slabs, quantity breaks and customer-specific rates without rewriting prices on every quotation." action="New price list" search={search} setSearch={setSearch} />
    <div className="pricing-demo"><div><span className="section-kicker">Price simulator</span><h3>Anchor 32A DP MCB</h3><p>Change quantity to see which B2B price rule applies.</p><label>Order quantity <input type="number" min="1" value={qty} onChange={(e)=>setQty(Math.max(1,Number(e.target.value)||1))}/></label></div><div><span>Applied rate</span><strong>{money(applied.price)}</strong><small>{applied.scheme || 'Standard rate'}</small><b>{qty} units = {money(qty*applied.price)}</b></div></div>
    <article className="panel module-panel"><div className="table-wrap"><table className="data-table module-table"><thead><tr><th>Price list</th><th>Customer</th><th>Product</th><th>Min qty</th><th>Rate</th><th>Discount</th><th>Scheme</th></tr></thead><tbody>{rules.map((r,i)=><tr key={`${r.list}-${r.sku}-${r.minQty}-${i}`}><td><strong>{r.list}</strong></td><td>{r.customer}</td><td><strong>{r.product}</strong><small>{r.sku}</small></td><td>{r.minQty}</td><td><strong>{money(r.price)}</strong></td><td>{r.discount}%</td><td>{r.scheme||'Standard'}</td></tr>)}</tbody></table></div></article>
  </div>;
}

export default function EnhancedModulePage({ module }) {
  if (module === 'purchases') return <PurchasesPage />;
  if (module === 'ledger') return <LedgerPage />;
  if (module === 'warehouses') return <WarehousesPage />;
  if (module === 'barcode') return <BarcodePage />;
  if (module === 'whatsapp') return <WhatsAppPage />;
  if (module === 'tax') return <TaxPage />;
  if (module === 'pricing') return <PricingPage />;
  return null;
}
