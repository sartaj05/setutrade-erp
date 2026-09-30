import { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { createApiResource } from '../services/api';
import { useApiData } from '../services/useApiData';
import { demoCustomers } from '../data/demoData';
import { demoWhatsAppDrafts } from '../data/featureData';

const money = (value) => `₹${Number(value || 0).toLocaleString('en-IN')}`;

export default function WhatsAppInboxPage() {
  const { mode } = useAuth();
  const fallback = { whatsapp: demoWhatsAppDrafts, messages: [], integration: { configured: false } };
  const { data, error, refresh } = useApiData('whatsapp', fallback);
  const customers = useApiData('customers', demoCustomers, 'customers');
  const [demoRows, setDemoRows] = useState(demoWhatsAppDrafts);
  const [customerId, setCustomerId] = useState('');
  const [message, setMessage] = useState('Need 20 Anchor 32A MCB and 10 Havells 12W LED bulbs');
  const [selected, setSelected] = useState(null);
  const [sendLive, setSendLive] = useState(false);
  const [notice, setNotice] = useState('');

  const rows = mode === 'api' ? (data?.whatsapp || []) : demoRows;
  const messages = mode === 'api' ? (data?.messages || []) : demoRows.map((row, index) => ({ id: row.id || index, customer: row.customer, direction: 'Inbound', message: row.message, status: 'Received', createdAt: new Date().toISOString() }));
  const parse = async () => {
    try {
      if (!customerId) return setNotice('Select a customer before capturing an order.');
      if (mode === 'api') {
        const result = await createApiResource('whatsapp', { customerId: Number(customerId), message, direction: 'Inbound' });
        setSelected(result.draft); refresh();
      } else {
        const customer = customers.data.find((row) => String(row.pk || row.id) === String(customerId));
        const next = { ...demoWhatsAppDrafts[0], id: `WA-DEMO-${Date.now().toString().slice(-5)}`, customer: customer?.name || 'Selected customer', message, status: 'Draft' };
        setDemoRows((current) => [next, ...current]); setSelected(next);
      }
      setNotice('Inbound message captured. Review the parsed lines before handoff.');
    } catch (e) { setNotice(e.message); }
  };
  const send = async () => {
    try {
      if (!customerId) return setNotice('Select a customer before sending a message.');
      if (mode === 'api') { await createApiResource('whatsapp', { customerId: Number(customerId), message, direction: 'Outbound', sendLive }); refresh(); }
      setNotice(sendLive ? 'WhatsApp delivery requested through the configured provider.' : 'Outbound message logged in the conversation history.');
    } catch (e) { setNotice(e.message); }
  };
  const handoff = async (row, action) => {
    try {
      if (mode === 'api') {
        const result = await createApiResource('whatsapp', { action, draftId: row.pk });
        setNotice(action === 'create-quotation' ? `Quotation ${result.quotationNo} created.` : `Order ${result.orderNo} created.`); refresh();
      } else {
        setDemoRows((current) => current.map((item) => item.id === row.id ? { ...item, status: action === 'create-quotation' ? 'Quoted' : 'Confirmed', ...(action === 'create-quotation' ? { quotationNo: 'QT-DEMO' } : { orderNo: 'SO-DEMO' }) } : item));
        setNotice(action === 'create-quotation' ? 'Demo quotation created from the inbox draft.' : 'Demo sales order created from the inbox draft.');
      }
    } catch (e) { setNotice(e.message); }
  };

  return <div>
    <div className="module-header"><div><span className="section-kicker">Conversational commerce</span><h1>WhatsApp order inbox</h1><p>Receive customer orders, review parsed lines, convert them into quotations or sales orders, and keep the conversation history attached to the customer.</p></div></div>
    {notice && <div className="inline-notice">{notice}</div>}
    {error && <div className="api-error"><strong>Live API issue</strong><span>{error}</span></div>}
    <div className="whatsapp-layout"><article className="chat-card"><div className="smart-form"><label>Customer<select value={customerId} onChange={(e) => setCustomerId(e.target.value)}><option value="">Select customer</option>{(customers.data || []).map((customer) => <option key={customer.pk || customer.id} value={customer.pk || customer.id}>{customer.name}</option>)}</select></label><label className="check-label"><input type="checkbox" checked={sendLive} onChange={(e) => setSendLive(e.target.checked)} />Use live WhatsApp provider</label></div><textarea value={message} onChange={(e) => setMessage(e.target.value)} placeholder="Paste an inbound order or write an outbound message"/><div className="row-actions"><button onClick={parse}>Capture inbound order</button><button className="secondary-btn" onClick={send}>Send message</button></div><small className="muted">Provider credentials are {data?.integration?.configured ? 'configured' : 'not configured'}; conversation logging is available in both modes.</small></article><article className="draft-card"><span className="section-kicker">Selected draft</span><h3>{selected?.id || 'No draft selected'}</h3><p>{selected?.customer || 'Choose a draft from the inbox below.'}</p>{(selected?.items || []).map((item) => <div className="list-row" key={item.sku}><span>{item.name}<small>{item.sku} · {item.quantity} units</small></span><strong>{money(item.quantity * item.price)}</strong></div>)}<div className="draft-total"><span>Estimated total</span><strong>{money(selected?.total)}</strong></div></article></div>
    <article className="panel module-panel"><div className="panel-head"><div><span>Order intake queue</span><h3>Drafts awaiting action</h3></div></div><div className="table-wrap"><table className="data-table module-table"><thead><tr><th>Draft</th><th>Customer</th><th>Message</th><th>Total</th><th>Status</th><th>Handoff</th></tr></thead><tbody>{rows.map((row) => <tr key={row.pk || row.id}><td><button className="table-action" onClick={() => setSelected(row)}>{row.id}</button></td><td>{row.customer}</td><td>{String(row.message).slice(0, 60)}</td><td>{money(row.total)}</td><td>{row.status}</td><td><div className="row-actions"><button className="table-action" disabled={!!row.quotationNo || !!row.orderNo} onClick={() => handoff(row, 'create-quotation')}>{row.quotationNo || 'Quotation'}</button><button className="table-action" disabled={!!row.orderNo} onClick={() => handoff(row, 'convert-order')}>{row.orderNo || 'Sales order'}</button></div></td></tr>)}</tbody></table></div></article>
    <article className="panel module-panel"><div className="panel-head"><div><span>Conversation history</span><h3>Customer messages</h3></div></div><div className="audit-list">{messages.map((row) => <div key={row.id}><span className="audit-action">{row.direction}</span><section><strong>{row.customer}</strong><small>{row.message}</small></section><time>{new Date(row.createdAt).toLocaleString('en-IN')}</time></div>)}</div></article>
  </div>;
}
