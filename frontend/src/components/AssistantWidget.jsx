import { useState } from 'react';
import { createApiResource } from '../services/api';
import { useAuth } from '../context/AuthContext';

const demoReply = (question) => {
  const q = question.toLowerCase();
  if (q.includes('shelf') || q.includes('shell') || q.includes('expiry') || q.includes('expire') || q.includes('last 1 day')) return 'Shelf life is not stored on the current product records. Add lot or batch expiry dates in Product Master / Traceability, and Setu can show days remaining and expiry alerts.';
  if (q.includes('stock') || q.includes('reorder')) return 'Polycab 2.5mm Wire and GM 8 Module Plate are the highest stock-risk items right now.';
  if (q.includes('overdue') || q.includes('collection')) return 'The largest overdue demo balances are Sethi Hardware House and NCR Buildmart.';
  if (q.includes('sales')) return 'Month-to-date demo sales are ₹42,86,400. You can ask me for a role-specific breakdown.';
  return 'I can help with sales, collections, stock risk, orders and purchase recommendations.';
};

export default function AssistantWidget({ hidden = false }) {
  const { user, mode } = useAuth();
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState([]);

  if (hidden) return null;

  const send = async (event) => {
    event.preventDefault();
    const question = input.trim();
    if (!question || busy) return;
    setMessages((rows) => [...rows, { role: 'user', content: question }]);
    setInput('');
    setBusy(true);
    try {
      const answer = mode === 'api'
        ? (await createApiResource('assistant', { question })).answer
        : demoReply(question);
      setMessages((rows) => [...rows, { role: 'assistant', content: answer }]);
    } catch (error) {
      setMessages((rows) => [...rows, { role: 'assistant', content: error.message || 'I could not complete that request.' }]);
    } finally {
      setBusy(false);
    }
  };

  return <div className={`assistant-widget ${open ? 'is-open' : ''}`}>
    {open && <section className="assistant-widget-panel" aria-label="Setu help assistant">
      <header className="assistant-widget-header">
        <div><strong>Setu</strong><span>Workspace help</span></div>
        <span className="assistant-online"><i /> Online</span>
      </header>
      <div className="assistant-widget-messages">
        {!messages.length && <div className="assistant-widget-welcome"><span className="assistant-bot">✦</span><p>Hi {user?.name?.split(' ')[0] || 'there'}! Ask me about sales, stock, collections, orders or expiry dates.</p></div>}
        {messages.map((message, index) => <div className={`assistant-widget-message ${message.role}`} key={`${message.role}-${index}`}><span>{message.role === 'assistant' ? 'Setu' : 'You'}</span><p>{message.content}</p></div>)}
        {busy && <div className="assistant-widget-message assistant"><span>Setu</span><p>Checking your workspace…</p></div>}
      </div>
      <form className="assistant-widget-compose" onSubmit={send}><input value={input} onChange={(event) => setInput(event.target.value)} placeholder="Ask for help…" aria-label="Ask Setu" /><button disabled={busy || !input.trim()} aria-label="Send question">↑</button></form>
    </section>}
    <button className="assistant-widget-toggle" onClick={() => setOpen((value) => !value)} aria-label={open ? 'Close Setu assistant' : 'Open Setu assistant'}>{open ? '×' : '✦'}<span>{open ? '' : 'Help'}</span></button>
  </div>;
}
