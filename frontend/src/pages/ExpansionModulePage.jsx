import { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { createApiResource, getApiResource } from '../services/api';
import { demoAutomations, demoChannels, demoCollections, demoNetworks, demoSupplierPortalAdmin, demoWms } from '../data/expansionData';

const money = (n) => `₹${Number(n || 0).toLocaleString('en-IN')}`;
const Notice = ({ children }) => children ? <div className="inline-notice">{children}</div> : null;
function Head({ eyebrow, title, text, action, actionLabel }) { return <div className="module-header"><div><span className="eyebrow">{eyebrow}</span><h1>{title}</h1><p>{text}</p></div>{action && <button onClick={action}>{actionLabel}</button>}</div>; }
function Table({ columns, rows }) { return <div className="table-wrap"><table className="data-table module-table"><thead><tr>{columns.map(c => <th key={c.key}>{c.label}</th>)}</tr></thead><tbody>{rows.map((r,i) => <tr key={r.id || i}>{columns.map(c => <td key={c.key}>{c.render ? c.render(r) : String(r[c.key] ?? '—')}</td>)}</tr>)}</tbody></table></div>; }

function Collections({ mode }) {
  const [data,setData]=useState(demoCollections); const [notice,setNotice]=useState('');
  useEffect(()=>{ if(mode==='api') getApiResource('collections').then(setData).catch(()=>{}); },[mode]);
  const collect=async()=>{ try { if(mode==='api') await createApiResource('collections',{action:'payment',customerId:1,amount:10000,method:'UPI',reference:`DEMO-${Date.now()}`}); setNotice('₹10,000 collection recorded and allocated to the oldest open invoice first.'); } catch(e){setNotice(e.message);} };
  return <><Head eyebrow="Cash conversion" title="Collections & reconciliation" text="Turn receivables into daily tasks, promises and invoice-matched payments." action={collect} actionLabel="Record demo collection"/><Notice>{notice}</Notice><div className="report-grid"><article><span>Total receivable</span><strong>{money(data.summary.receivable)}</strong><small>customer balances</small></article><article><span>Open collection tasks</span><strong>{data.summary.openTasks}</strong><small>sales follow-ups</small></article><article><span>Promise to pay</span><strong>{money(data.summary.promiseAmount)}</strong><small>{data.summary.unmatched} unmatched payment(s)</small></article></div><article className="panel module-panel"><div className="panel-head"><div><span>Priority queue</span><h3>Collection tasks</h3></div></div><Table columns={[{key:'customer',label:'Customer'},{key:'amount',label:'Amount',render:r=>money(r.amount)},{key:'due',label:'Due'},{key:'priority',label:'Priority'},{key:'assignee',label:'Owner'},{key:'status',label:'Status'}]} rows={data.tasks}/></article><article className="panel module-panel"><div className="panel-head"><div><span>Bank / UPI feed</span><h3>Reconciliation</h3></div></div><Table columns={[{key:'reference',label:'Reference'},{key:'customer',label:'Customer'},{key:'amount',label:'Amount',render:r=>money(r.amount)},{key:'method',label:'Method'},{key:'status',label:'Match'}]} rows={data.transactions}/></article></>;
}

function Wms({ mode }) {
  const [data,setData]=useState(demoWms); const [notice,setNotice]=useState('');
  useEffect(()=>{ if(mode==='api') getApiResource('wms').then(setData).catch(()=>{}); },[mode]);
  const createBin=async()=>{ try { if(mode==='api') await createApiResource('wms',{action:'create-bin',warehouseId:1,code:`A-${Date.now().toString().slice(-4)}`,zone:'Fast Moving',capacity:100}); setNotice('New bin created.'); } catch(e){setNotice(e.message);} };
  return <><Head eyebrow="Warehouse execution" title="Advanced WMS" text="Bin locations, release-to-pick, waves, packing and cycle counts for tighter stock accuracy." action={createBin} actionLabel="Create demo bin"/><Notice>{notice}</Notice><div className="report-grid"><article><span>Active bins</span><strong>{data.bins.length}</strong><small>location controlled</small></article><article><span>Open picks</span><strong>{data.picks.filter(x=>x.status!=='Complete').length}</strong><small>warehouse work</small></article><article><span>Waves / packs</span><strong>{(data.waves||[]).length} / {(data.packing||[]).length}</strong><small>batch pick and dispatch prep</small></article></div><article className="panel module-panel"><Table columns={[{key:'pickNo',label:'Pick list'},{key:'warehouse',label:'Warehouse'},{key:'lines',label:'Lines'},{key:'status',label:'Status'}]} rows={data.picks}/></article><div className="wms-split"><article className="panel module-panel"><div className="panel-head"><div><span>Batch picking</span><h3>Waves</h3></div></div><Table columns={[{key:'waveNo',label:'Wave'},{key:'warehouse',label:'Warehouse'},{key:'pickCount',label:'Picks'},{key:'status',label:'Status'}]} rows={data.waves||[]}/></article><article className="panel module-panel"><div className="panel-head"><div><span>Dispatch prep</span><h3>Packing</h3></div></div><Table columns={[{key:'packageNo',label:'Package'},{key:'order',label:'Order'},{key:'cartons',label:'Cartons'},{key:'status',label:'Status'}]} rows={data.packing||[]}/></article></div><article className="panel module-panel"><Table columns={[{key:'code',label:'Bin'},{key:'zone',label:'Zone'},{key:'warehouse',label:'Warehouse'},{key:'capacity',label:'Capacity'}]} rows={data.bins}/></article></>;
}

function SupplierAdmin({ mode }) {
  const [data,setData]=useState(demoSupplierPortalAdmin);
  useEffect(()=>{ if(mode==='api') getApiResource('supplier-portal-admin').then(setData).catch(()=>{}); },[mode]);
  return <><Head eyebrow="Vendor collaboration" title="Supplier portal inbox" text="Track supplier PO confirmations, delivery ETAs, invoice uploads and notes without email archaeology."/><article className="panel module-panel"><Table columns={[{key:'supplier',label:'Supplier'},{key:'po',label:'PO'},{key:'type',label:'Submission'},{key:'status',label:'Status'},{key:'payload',label:'Detail',render:r=>JSON.stringify(r.payload)}]} rows={data.submissions}/></article></>;
}

function Automations({ mode }) {
  const [data,setData]=useState(demoAutomations); const [notice,setNotice]=useState('');
  useEffect(()=>{ if(mode==='api') getApiResource('automations').then(setData).catch(()=>{}); },[mode]);
  const test=async()=>{ try { const r=mode==='api'?await createApiResource('automations',{action:'test',event:'invoice.overdue',payload:{outstanding:85000,customerId:1},entityType:'Customer',entityId:'1'}):{matched:1}; setNotice(`${r.matched} rule(s) matched. Operational actions executed.`); } catch(e){setNotice(e.message);} };
  return <><Head eyebrow="No-code operations" title="Workflow automation" text="Define event + condition + action rules for collections, stock, approvals and notifications." action={test} actionLabel="Test overdue event"/><Notice>{notice}</Notice><div className="automation-cards">{data.rules.map(r=><article className="panel rule-card" key={r.id}><span className="eyebrow">{r.event}</span><h3>{r.name}</h3><code>{JSON.stringify(r.conditions)}</code><p>{r.actions.map(a=>a.type).join(' → ')}</p><strong>{r.active?'Active':'Paused'}</strong></article>)}</div><article className="panel module-panel"><Table columns={[{key:'rule',label:'Rule'},{key:'event',label:'Event'},{key:'actions',label:'Actions',render:r=>r.actions.join(', ')},{key:'status',label:'Status'}]} rows={data.runs}/></article></>;
}

function Channels({ mode }) {
  const [data,setData]=useState(demoChannels); const [notice,setNotice]=useState('');
  useEffect(()=>{ if(mode==='api') getApiResource('channels').then(setData).catch(()=>{}); },[mode]);
  const ingest=async()=>{ try { if(mode==='api') await createApiResource('channels',{action:'ingest-order',channelId:data.channels[0]?.id,externalId:`WEB-${Date.now()}`,customerName:'Demo Web Buyer',phone:'9811000000',total:5841,items:[{sku:'AN-MCB-32',name:'Anchor 32A DP MCB',quantity:10,unitPrice:495}]}); setNotice('External order ingested idempotently and SKU matching attempted.'); } catch(e){setNotice(e.message);} };
  return <><Head eyebrow="Omnichannel order intake" title="External sales channels" text="Normalize website, ONDC and marketplace orders into one review queue before ERP conversion." action={ingest} actionLabel="Simulate web order"/><Notice>{notice}</Notice><div className="channel-grid">{data.channels.map(c=><article className="panel" key={c.id}><span className="eyebrow">{c.provider}</span><h3>{c.name}</h3><p>{c.storeId || 'Credentials pending'}</p><strong>{c.active?'Connected':'Setup required'}</strong></article>)}</div><article className="panel module-panel"><Table columns={[{key:'externalId',label:'External order'},{key:'channel',label:'Channel'},{key:'customer',label:'Customer'},{key:'total',label:'Total',render:r=>money(r.total)},{key:'status',label:'Status'}]} rows={data.orders}/></article></>;
}

function Networks({ mode }) {
  const [data,setData]=useState(demoNetworks); const [notice,setNotice]=useState('');
  useEffect(()=>{ if(mode==='api') getApiResource('distribution-networks').then(setData).catch(()=>{}); },[mode]);
  const network=data.ownedNetworks?.[0];
  return <><Head eyebrow="Secondary-sales visibility" title="Distributor network" text="Share agreed stock and secondary-sales summaries across a manufacturer/distributor network without exposing customer-level data."/><Notice>{notice}</Notice>{network?<><div className="module-header compact"><div><h2>{network.name}</h2><p>Network code {network.code}</p></div></div><div className="network-grid">{network.members.map(m=><article className="panel network-card" key={m.id}><span className="eyebrow">{m.region} · {m.territory}</span><h3>{m.company}</h3><strong>{money(m.snapshot?.secondarySales)}</strong><small>secondary sales</small><div><span>Inventory</span><b>{money(m.snapshot?.inventoryValue)}</b></div><div><span>Open orders</span><b>{m.snapshot?.openOrders ?? '—'}</b></div><p>Privacy: aggregate stock/sales only</p></article>)}</div></>:<article className="panel module-panel"><p>No owned network yet. Create one through the API or onboarding flow.</p></article>}</>;
}

export default function ExpansionModulePage({ module }) {
  const { mode } = useAuth();
  if(module==='collections') return <Collections mode={mode}/>;
  if(module==='wms') return <Wms mode={mode}/>;
  if(module==='supplier-portal-admin') return <SupplierAdmin mode={mode}/>;
  if(module==='automations') return <Automations mode={mode}/>;
  if(module==='channels') return <Channels mode={mode}/>;
  if(module==='distribution-network') return <Networks mode={mode}/>;
  return null;
}
