import { useMemo, useState } from 'react';
import { createApiResource } from '../services/api';
import { useAuth } from '../context/AuthContext';

const rolePrompts = {
  OWNER: ['What needs my attention today?', 'Show overdue customers', 'Which products may run out?'],
  MANAGER: ['What orders are waiting?', 'Show low-stock products', 'Which returns need review?'],
  SALES: ['Show today’s orders', 'Which customers are overdue?', 'What should I follow up on?'],
  WAREHOUSE: ['Show low-stock products', 'Which lots expire soon?', 'What is ready to dispatch?'],
  ACCOUNTANT: ['Show this month’s collections', 'Which invoices are overdue?', 'Show pending approvals'],
};

function demoReply(question) {
  const q = question.toLowerCase();
  if (q.includes('shelf') || q.includes('shell') || q.includes('expiry') || q.includes('expire') || q.includes('last 1 day')) return { answer: 'Shelf life is not stored on the current product records. Add lot or batch expiry dates in Product Master / Traceability and Setu can show days remaining and expiry alerts.', intent: 'expiry', data: { lots: [], nextStep: 'Record lot or batch expiry dates.' } };
  if (q.includes('stock') || q.includes('reorder') || q.includes('run out')) return { answer: 'Polycab 2.5mm Wire and GM 8 Module Plate are the highest stock-risk items right now.', intent: 'stock-risk', data: { products: [{ name: 'Polycab 2.5mm Wire Red', stock: 7, reorderLevel: 12 }, { name: 'GM 8 Module Plate', stock: 12, reorderLevel: 15 }] } };
  if (q.includes('overdue') || q.includes('receivable') || q.includes('collection')) return { answer: 'The largest overdue demo balances are Sethi Hardware House and NCR Buildmart.', intent: 'receivables', data: { customers: [{ name: 'Sethi Hardware House', outstanding: 124600 }, { name: 'NCR Buildmart', outstanding: 76750 }] } };
  if (q.includes('order') || q.includes('dispatch')) return { answer: 'There are 34 open demo orders, with 7 waiting for dispatch.', intent: 'orders', data: { openOrders: 34, waitingDispatch: 7 } };
  if (q.includes('return') || q.includes('damage')) return { answer: 'There are 3 recent demo returns and 2 stock adjustments that need review.', intent: 'returns', data: { returns: 3, adjustments: 2 } };
  if (q.includes('warehouse') || q.includes('location')) return { answer: 'The demo workspace has 3 active warehouses: Delhi Central, Noida Hub and Gurugram Depot.', intent: 'warehouses', data: { warehouses: 3 } };
  if (q.includes('sales') || q.includes('revenue')) return { answer: 'Month-to-date demo sales are ₹42,86,400. I can also open the sales dashboard for the full breakdown.', intent: 'sales', data: { sales: 4286400 } };
  return { answer: 'I can help with sales, orders, stock, collections, returns, warehouses, expiry dates and purchase recommendations. Try one of the suggested questions below.', intent: 'help', data: {} };
}

const intentActions = {
  sales: ['Open overview', 'dashboard'],
  orders: ['Open orders', 'orders'],
  'stock-risk': ['Open inventory', 'inventory'],
  receivables: ['Open credit ledger', 'ledger'],
  collections: ['Open payments', 'payments'],
  returns: ['Review returns', 'returns'],
  expiry: ['Open traceability', 'traceability'],
  warehouses: ['Open warehouses', 'warehouses'],
  approvals: ['Review approvals', 'approvals'],
  forecast: ['Open forecasting', 'forecasting'],
};

const money = (value) => `₹${Number(value || 0).toLocaleString('en-IN')}`;

export default function AssistantWidget({ hidden = false, navigate, onModuleChange, visibleModules = [] }) {
  const { user, mode } = useAuth();
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [input, setInput] = useState('');
  const [threadId, setThreadId] = useState(null);
  const [messages, setMessages] = useState([]);
  const prompts = useMemo(() => rolePrompts[user?.role] || rolePrompts.OWNER, [user?.role]);

  if (hidden) return null;

  const ask = async (question) => {
    const value = question.trim();
    if (!value || busy) return;
    setMessages((rows) => [...rows, { role: 'user', content: value }]);
    setInput('');
    setBusy(true);
    try {
      const result = mode === 'api'
        ? await createApiResource('assistant', { question: value, ...(threadId ? { threadId } : {}) })
        : demoReply(value);
      if (result.threadId) setThreadId(result.threadId);
      setMessages((rows) => [...rows, { role: 'assistant', content: result.answer, intent: result.intent, data: result.data }]);
    } catch (error) {
      setMessages((rows) => [...rows, { role: 'assistant', content: error.message || 'I could not complete that request.', intent: 'error' }]);
    } finally {
      setBusy(false);
    }
  };

  const send = (event) => { event.preventDefault(); ask(input); };
  const openModule = (module) => {
    if (!visibleModules.includes(module)) return;
    onModuleChange(module);
    navigate('/app');
    setOpen(false);
  };
  const clearConversation = () => { setMessages([]); setThreadId(null); };

  return <div className={`assistant-widget ${open ? 'is-open' : ''}`}>
    {open && <section className="assistant-widget-panel" aria-label="Setu operations assistant">
      <header className="assistant-widget-header">
        <div><strong>Setu</strong><span>Operations copilot · {mode === 'api' ? 'Live workspace' : 'Demo workspace'}</span></div>
        <div className="assistant-widget-header-actions"><span className="assistant-online"><i /> {mode === 'api' ? 'Live' : 'Demo'}</span><button onClick={clearConversation} aria-label="Clear conversation">↺</button></div>
      </header>
      <div className="assistant-widget-messages">
        {!messages.length && <div className="assistant-widget-welcome"><span className="assistant-bot">✦</span><div><p>Hi {user?.name?.split(' ')[0] || 'there'}! I can help with your SetuStock workspace.</p><div className="assistant-prompt-list">{prompts.map((prompt) => <button key={prompt} onClick={() => ask(prompt)}>{prompt}</button>)}</div></div></div>}
        {messages.map((message, index) => <div className={`assistant-widget-message ${message.role}`} key={`${message.role}-${index}`}><span>{message.role === 'assistant' ? 'Setu' : 'You'}</span><p>{message.content}</p>{message.role === 'assistant' && message.data && <div className="assistant-data-card">
          {message.data.products?.map((product) => <div key={product.name}><strong>{product.name}</strong><small>{product.stock} available · reorder at {product.reorderLevel}</small></div>)}
          {message.data.customers?.map((customer) => <div key={customer.name}><strong>{customer.name}</strong><small>{money(customer.outstanding)} outstanding</small></div>)}
          {message.data.lots?.map((lot) => <div key={lot.lot}><strong>{lot.product} · {lot.lot}</strong><small>{lot.daysRemaining} days remaining</small></div>)}
          {message.data.warehouses?.map((warehouse) => <div key={warehouse.name}><strong>{warehouse.name}</strong><small>{warehouse.city}</small></div>)}
          {message.data.openOrders && <div><strong>{message.data.openOrders} open orders</strong><small>{message.data.waitingDispatch} waiting for dispatch</small></div>}
          {message.data.returns && <div><strong>{message.data.returns} returns</strong><small>{message.data.adjustments} stock adjustments to review</small></div>}
          {message.data.pending !== undefined && <div><strong>{message.data.pending} approvals pending</strong><small>Review before execution</small></div>}
          {message.data.sales && <div><strong>{money(message.data.sales)} sales</strong><small>Month to date</small></div>}
          {message.data.nextStep && <small className="assistant-next-step">Next step: {message.data.nextStep}</small>}
        </div>}{message.role === 'assistant' && intentActions[message.intent] && visibleModules.includes(intentActions[message.intent][1]) && <button className="assistant-action-link" onClick={() => openModule(intentActions[message.intent][1])}>{intentActions[message.intent][0]} ↗</button>}</div>)}
        {busy && <div className="assistant-widget-message assistant"><span>Setu</span><p>Checking your workspace…</p></div>}
      </div>
      <div className="assistant-widget-suggestions">{messages.length > 0 && prompts.slice(0, 2).map((prompt) => <button key={prompt} onClick={() => ask(prompt)}>{prompt}</button>)}</div>
      <form className="assistant-widget-compose" onSubmit={send}><input value={input} onChange={(event) => setInput(event.target.value)} placeholder="Ask about your business…" aria-label="Ask Setu" /><button disabled={busy || !input.trim()} aria-label="Send question">↑</button></form>
    </section>}
    <button className="assistant-widget-toggle" onClick={() => setOpen((value) => !value)} aria-label={open ? 'Close Setu assistant' : 'Open Setu assistant'}>{open ? '×' : '✦'}<span>{open ? '' : 'Help'}</span></button>
  </div>;
}
