import { useEffect, useState } from 'react';
import { getApiResource } from '../services/api';
import { useAuth } from '../context/AuthContext';

const demoSteps = [
  ['Customer enquiry', 'Complete', 'R.K. Trading Co.'], ['Quotation', 'Accepted', 'QT-2026-044'], ['Sales order', 'Ready', 'SO-1097'],
  ['Stock reservation', 'Reserved', 'Delhi Central'], ['GST invoice', 'Unpaid', 'INV-2026-1184'], ['Payment', 'Pending', 'Awaiting receipt'],
  ['Delivery / e-POD', 'Scheduled', 'RUN-028'], ['Customer ledger', 'Posted', 'INV-2026-1184'],
];

export default function ClientWorkflowPage() {
  const { mode } = useAuth();
  const [data, setData] = useState({ steps: demoSteps.map(([label, status, detail], index) => ({ key: index, label, status, detail })) });
  const [error, setError] = useState('');
  const load = () => { if (mode !== 'api') return; setError(''); getApiResource('client-workflow').then(setData).catch((err) => setError(err.message || 'Workflow could not be loaded.')); };
  useEffect(load, [mode]);
  const completed = data.steps.filter((step) => ['Complete', 'Accepted', 'Ready', 'Reserved', 'Posted', 'Paid', 'Delivered'].includes(step.status)).length;
  return <div className="workflow-page">
    <div className="module-header"><div><span className="section-kicker">Client delivery view</span><h1>Order-to-cash control room</h1><p>Follow one customer journey from enquiry to cash, delivery proof and ledger posting.</p></div><div className="module-actions"><button className="secondary-btn" onClick={load}>Refresh live workflow</button></div></div>
    {error && <div className="api-error"><strong>Live workflow unavailable</strong><span>{error}</span><small>Production mode keeps the state visible and does not replace it with demo records.</small></div>}
    <section className="workflow-progress"><div><span>Journey progress</span><strong>{completed} of {data.steps.length} checkpoints complete</strong></div><div className="progress-track"><i style={{ width: `${Math.round(completed / Math.max(1, data.steps.length) * 100)}%` }} /></div><small>{data.context?.customer ? `${data.context.customer} · ${data.context.order || 'new order'}` : 'Demo storyline · connect Django to show company data'}</small></section>
    <article className="panel module-panel workflow-panel"><div className="panel-head"><div><span>Golden path</span><h3>Every handoff has an owner</h3></div><span className="feature-badge">Live workflow</span></div><div className="workflow-steps">{data.steps.map((step, index) => <div className="workflow-step" key={step.key || index}><span className="workflow-number">{String(index + 1).padStart(2, '0')}</span><div><strong>{step.label}</strong><small>{step.detail}</small></div><em className={`workflow-status ${String(step.status).toLowerCase().replace(/\s+/g, '-')}`}>{step.status}</em></div>)}</div></article>
    <div className="workflow-next"><div><span>Next recommended action</span><strong>{data.steps.find((step) => !['Complete', 'Accepted', 'Ready', 'Reserved', 'Posted', 'Paid', 'Delivered'].includes(step.status))?.label || 'Review the completed journey'}</strong><p>Use the status trail to make the next operational handoff obvious for the team.</p></div><button onClick={load}>Check latest status →</button></div>
  </div>;
}
