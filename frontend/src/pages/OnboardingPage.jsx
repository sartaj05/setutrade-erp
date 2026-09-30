import { useEffect, useMemo, useState } from 'react';
import {
  commitImport,
  createApiResource,
  getApiResource,
  previewImport,
  rollbackImport,
  submitOnboardingFeedback,
} from '../services/api';
import { useAuth } from '../context/AuthContext';

const demo = {
  company: { name: 'Khanna Electrical Distributors', gstin: '09AABCK1234A1Z5', state: 'Delhi' },
  checklist: { companyProfile: true, gstin: true, branches: 2, warehouses: 3, users: 5, products: 6, customers: 5, suppliers: 2, openingBalances: true },
};

const labels = {
  companyProfile: 'Company profile', gstin: 'GSTIN and tax identity', branches: 'Operating branches',
  warehouses: 'Warehouses', users: 'Team users', products: 'Product catalogue', customers: 'Customer accounts', suppliers: 'Supplier accounts', openingBalances: 'Opening balances',
};

const steps = [
  ['Company profile', 'Set the legal identity and tax details used across invoices.'],
  ['Locations & team', 'Add branches, warehouses, and the first client users.'],
  ['Import client data', 'Map and validate approved products, customers, suppliers, stock, and balances.'],
  ['Go-live review', 'Confirm the checklist and capture client feedback before handoff.'],
];

const importResources = [
  ['products', 'Products', 'SKU, pricing, GST, barcode, and reorder settings'],
  ['customers', 'Customers', 'Dealer accounts, GSTIN, credit limits, and contacts'],
  ['suppliers', 'Suppliers', 'Supplier master, GSTIN, payment contacts, and locations'],
  ['opening-stock', 'Opening stock', 'Warehouse balances by SKU and reserved quantity'],
  ['opening-balances', 'Opening balances', 'Customer receivables and opening ledger entries'],
];

const emptyFeedback = { rating: 0, workflow: 'Overall onboarding', workedWell: '', blockers: '', externalTools: '', dataTrust: 0, offlineNeeds: '', dailyReport: '', requestedFeatures: '', wouldRecommend: true };

export default function OnboardingPage() {
  const { mode } = useAuth();
  const [data, setData] = useState(demo);
  const [imports, setImports] = useState([]);
  const [resources, setResources] = useState({});
  const [step, setStep] = useState(0);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState('');
  const [company, setCompany] = useState(demo.company);
  const [branch, setBranch] = useState({ code: '', name: '', city: '' });
  const [warehouse, setWarehouse] = useState({ code: '', name: '', city: '' });
  const [team, setTeam] = useState({ name: '', email: '', role: 'SALES', temporaryPassword: '' });
  const [importResource, setImportResource] = useState('products');
  const [importFile, setImportFile] = useState(null);
  const [mapping, setMapping] = useState({});
  const [preview, setPreview] = useState(null);
  const [feedback, setFeedback] = useState(emptyFeedback);

  const load = async () => {
    if (mode !== 'api') return;
    try {
      const [next, history] = await Promise.all([getApiResource('onboarding'), getApiResource('imports')]);
      setData(next); setCompany(next.company || {}); setImports(history.imports || []); setResources(history.resources || {});
    } catch (err) { setNotice(err.message); }
  };

  useEffect(() => { load(); }, [mode]);

  const checks = useMemo(() => Object.entries(data.checklist || {}).map(([key, value]) => ({
    key, label: labels[key] || key, value, complete: typeof value === 'number' ? value > 0 : Boolean(value),
  })), [data]);

  const send = async (action, payload = {}) => {
    setBusy(true);
    try {
      if (mode === 'api') await createApiResource('onboarding', { action, ...payload });
      setNotice(action === 'seed-demo' ? 'Demo workspace records are ready for review.' : action === 'complete' ? 'Onboarding completed. Workspace is ready for client handoff.' : 'Step saved.');
      await load();
    } catch (err) { setNotice(err.message); } finally { setBusy(false); }
  };

  const saveStep = async () => {
    if (step === 0) await send('update-company', company);
    if (step === 1) {
      if (branch.code || branch.name) await send('create-branch', branch);
      if (warehouse.code || warehouse.name) await send('create-warehouse', warehouse);
      if (team.name || team.email) {
        if (mode === 'api') await createApiResource('team', team);
        setTeam({ name: '', email: '', role: 'SALES', temporaryPassword: '' });
        setNotice('Team member created. Ask the user to change the temporary password after first sign-in.');
      }
      await load();
    }
    if (step === 2) await load();
    if (step === 3) await send('complete');
    if (step < steps.length - 1) setStep(step + 1);
  };

  const runPreview = async () => {
    if (!importFile) return setNotice('Choose a CSV or XLSX file first.');
    setBusy(true);
    try {
      if (mode !== 'api') throw new Error('Connect Django to preview and import client data.');
      const next = await previewImport(importResource, importFile, mapping);
      setPreview(next); setMapping(next.mapping || {});
      setNotice(next.errors ? `${next.errors} validation issue(s) found. Fix the mapping or file before importing.` : 'Preview is ready. Review the mapping and commit when approved.');
    } catch (err) { setNotice(err.message); } finally { setBusy(false); }
  };

  const commit = async () => {
    setBusy(true);
    try {
      const next = await commitImport(preview.id);
      setPreview(next); setNotice(`Import completed: ${next.created} created and ${next.updated} updated.`); await load();
    } catch (err) { setNotice(err.message); } finally { setBusy(false); }
  };

  const rollback = async (id) => {
    setBusy(true);
    try { await rollbackImport(id); setNotice('Import rolled back successfully.'); await load(); } catch (err) { setNotice(err.message); } finally { setBusy(false); }
  };

  const submitFeedback = async (event) => {
    event.preventDefault();
    if (!feedback.rating) return setNotice('Select a rating before submitting feedback.');
    setBusy(true);
    try {
      if (mode === 'api') await submitOnboardingFeedback(feedback);
      setNotice('Thank you. The client feedback has been recorded for the next enhancement cycle.');
      setFeedback(emptyFeedback);
    } catch (err) { setNotice(err.message); } finally { setBusy(false); }
  };

  const complete = checks.filter((item) => item.complete).length;
  const fieldDefinitions = resources[importResource]?.fields || [];

  return <div className="onboarding-page">
    <div className="module-header"><div><span className="section-kicker">Client readiness</span><h1>Onboarding & data migration</h1><p>Set up a client workspace, validate approved source data, and collect feedback before go-live.</p></div><span className="feature-badge">{complete}/{checks.length} ready</span></div>
    {notice && <div className="inline-notice">{notice}</div>}
    <div className="onboarding-stepper">{steps.map(([title], index) => <button key={title} className={index === step ? 'active' : index < step ? 'complete' : ''} onClick={() => setStep(index)}><b>0{index + 1}</b><span>{title}</span></button>)}</div>
    <section className="onboarding-hero"><div><span>Workspace</span><strong>{data.company?.name || 'New client workspace'}</strong><small>{data.company?.state || 'State not set'} · {data.company?.gstin || 'GSTIN not added'}</small></div><div><span>Current step</span><strong>{steps[step][0]}</strong><small>{steps[step][1]}</small></div></section>

    <article className="panel module-panel onboarding-wizard">
      <div className="panel-head"><div><span>Step {step + 1} of {steps.length}</span><h3>{steps[step][0]}</h3></div></div>

      {step === 0 && <div className="smart-form onboarding-form-grid"><label>Company name<input value={company.name || ''} onChange={(e) => setCompany({ ...company, name: e.target.value })} required /></label><label>GSTIN<input value={company.gstin || ''} onChange={(e) => setCompany({ ...company, gstin: e.target.value.toUpperCase() })} /></label><label>State<input value={company.state || ''} onChange={(e) => setCompany({ ...company, state: e.target.value })} required /></label><label>Address<input value={company.address || ''} onChange={(e) => setCompany({ ...company, address: e.target.value })} /></label><label>Phone<input value={company.phone || ''} onChange={(e) => setCompany({ ...company, phone: e.target.value })} /></label><label>Email<input type="email" value={company.email || ''} onChange={(e) => setCompany({ ...company, email: e.target.value })} /></label></div>}

      {step === 1 && <div className="onboarding-location-grid"><div className="smart-form"><h4>Add branch</h4><label>Code<input value={branch.code} onChange={(e) => setBranch({ ...branch, code: e.target.value })} placeholder="HQ" /></label><label>Name<input value={branch.name} onChange={(e) => setBranch({ ...branch, name: e.target.value })} placeholder="Delhi Central" /></label><label>City<input value={branch.city} onChange={(e) => setBranch({ ...branch, city: e.target.value })} /></label></div><div className="smart-form"><h4>Add warehouse</h4><label>Code<input value={warehouse.code} onChange={(e) => setWarehouse({ ...warehouse, code: e.target.value })} placeholder="MAIN" /></label><label>Name<input value={warehouse.name} onChange={(e) => setWarehouse({ ...warehouse, name: e.target.value })} placeholder="Main Warehouse" /></label><label>City<input value={warehouse.city} onChange={(e) => setWarehouse({ ...warehouse, city: e.target.value })} /></label></div><div className="smart-form onboarding-team-form"><h4>Invite first team user</h4><label>Name<input value={team.name} onChange={(e) => setTeam({ ...team, name: e.target.value })} placeholder="Priya Sharma" /></label><label>Email<input type="email" value={team.email} onChange={(e) => setTeam({ ...team, email: e.target.value })} placeholder="priya@client.com" /></label><label>Role<select value={team.role} onChange={(e) => setTeam({ ...team, role: e.target.value })}><option value="MANAGER">Manager</option><option value="SALES">Sales</option><option value="WAREHOUSE">Warehouse</option><option value="ACCOUNTANT">Accountant</option></select></label><label>Temporary password<input value={team.temporaryPassword} onChange={(e) => setTeam({ ...team, temporaryPassword: e.target.value })} placeholder="Optional" /></label></div></div>}

      {step === 2 && <div className="migration-workspace"><div className="migration-toolbar"><label>Data type<select value={importResource} onChange={(e) => { setImportResource(e.target.value); setPreview(null); setMapping({}); }}>{importResources.map(([key, title]) => <option value={key} key={key}>{title}</option>)}</select></label><label>CSV or Excel file<input type="file" accept=".csv,.xlsx,text/csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" onChange={(e) => { setImportFile(e.target.files?.[0] || null); setPreview(null); }} /></label><button onClick={runPreview} disabled={busy || !importFile}>{busy ? 'Checking...' : 'Preview & validate'}</button><button className="secondary-btn" onClick={() => send('seed-demo')} disabled={busy}>Prepare demo data</button></div><p className="muted migration-help">Upload approved client data only. The preview never changes live records; commit creates an auditable import batch that can be rolled back.</p>{preview && <div className="import-preview"><div className="import-summary"><div><span>Rows</span><strong>{preview.rows}</strong></div><div><span>Validation issues</span><strong className={preview.errors ? 'text-danger' : 'text-success'}>{preview.errors}</strong></div><div><span>Existing records</span><strong>{preview.duplicates}</strong></div><div><span>Status</span><strong>{preview.status}</strong></div></div><div className="mapping-grid">{fieldDefinitions.map((field) => <label key={field.key}>{field.label}{field.required && <em> required</em>}<select value={mapping[field.key] || ''} onChange={(e) => setMapping({ ...mapping, [field.key]: e.target.value })}><option value="">Not mapped</option>{(preview.headers || []).map((header) => <option key={header} value={header}>{header}</option>)}</select></label>)}</div>{preview.validationErrors?.length > 0 && <div className="import-errors"><strong>Validation errors</strong>{preview.validationErrors.slice(0, 12).map((error, index) => <span key={`${error.row}-${error.field}-${index}`}>Row {error.row}: {error.field} - {error.message}</span>)}</div>}{preview.duplicateRows?.length > 0 && <div className="import-duplicates"><strong>Existing records will be updated or skipped</strong>{preview.duplicateRows.slice(0, 8).map((row, index) => <span key={`${row.key}-${index}`}>Row {row.row}: {row.key} ({row.action})</span>)}</div>}<div className="row-actions"><button className="secondary-btn" onClick={runPreview} disabled={busy}>Recheck mapping</button>{preview.status === 'Ready' && <button onClick={commit} disabled={busy}>{busy ? 'Importing...' : 'Commit import'}</button>}</div></div>}<div className="import-history"><div className="panel-head"><div><span>Audit history</span><h3>Recent import batches</h3></div></div>{imports.length === 0 && <p className="muted">No import batches yet.</p>}{imports.map((item) => <div className="import-history-row" key={item.id}><div><strong>{item.label}</strong><small>{item.filename} · {item.rows} rows · {item.created} created · {item.updated} updated</small></div><span className={`status-pill ${item.status.toLowerCase().replaceAll(' ', '-')}`}>{item.status}</span>{item.status === 'Completed' && <button className="secondary-btn" onClick={() => rollback(item.id)} disabled={busy}>Rollback</button>}</div>)}</div></div>}

      {step === 3 && <div className="onboarding-review"><p>Review every checkpoint below. Missing items should be completed before enabling client users.</p>{checks.map((item) => <div key={item.key} className={item.complete ? 'onboarding-check complete' : 'onboarding-check'}><span>{item.complete ? '✓' : '!'}</span><div><strong>{item.label}</strong><small>{typeof item.value === 'number' ? `${item.value} records configured` : item.complete ? 'Configured and ready' : 'Required before go-live'}</small></div><em>{item.complete ? 'Ready' : 'Needs setup'}</em></div>)}<form className="feedback-form" onSubmit={submitFeedback}><div><span className="section-kicker">Client feedback</span><h4>What should we improve next?</h4><p>Capture the client’s first-hand experience before starting the next feature cycle.</p></div><label>Workflow<select value={feedback.workflow} onChange={(e) => setFeedback({ ...feedback, workflow: e.target.value })}><option>Overall onboarding</option><option>Company setup</option><option>Team and access</option><option>Data import</option><option>Go-live review</option></select></label><label>Rating<select value={feedback.rating} onChange={(e) => setFeedback({ ...feedback, rating: Number(e.target.value) })}><option value="0">Select rating</option><option value="5">5 - Excellent</option><option value="4">4 - Good</option><option value="3">3 - Acceptable</option><option value="2">2 - Difficult</option><option value="1">1 - Blocked</option></select></label><label>What worked well<textarea value={feedback.workedWell} onChange={(e) => setFeedback({ ...feedback, workedWell: e.target.value })} placeholder="Which workflow felt useful?" /></label><label>Where did you get stuck?<textarea value={feedback.blockers} onChange={(e) => setFeedback({ ...feedback, blockers: e.target.value })} placeholder="Which step stopped or slowed you?" /></label><label>Which outside tools are still required?<textarea value={feedback.externalTools} onChange={(e) => setFeedback({ ...feedback, externalTools: e.target.value })} placeholder="Excel, WhatsApp, paper, another accounting app..." /></label><label>Trust in payment, GST, stock and outstanding figures<select value={feedback.dataTrust} onChange={(e) => setFeedback({ ...feedback, dataTrust: Number(e.target.value) })}><option value="0">Select confidence</option><option value="5">5 - Fully trust</option><option value="4">4 - Mostly trust</option><option value="3">3 - Need verification</option><option value="2">2 - Often question it</option><option value="1">1 - Do not trust yet</option></select></label><label>What must work offline on mobile?<textarea value={feedback.offlineNeeds} onChange={(e) => setFeedback({ ...feedback, offlineNeeds: e.target.value })} placeholder="Orders, visits, collections, delivery proof..." /></label><label>Which report or notification is needed every day?<textarea value={feedback.dailyReport} onChange={(e) => setFeedback({ ...feedback, dailyReport: e.target.value })} placeholder="Daily sales, overdue payments, stock risk..." /></label><label>Requested features<textarea value={feedback.requestedFeatures} onChange={(e) => setFeedback({ ...feedback, requestedFeatures: e.target.value })} placeholder="What should be built next?" /></label><label className="feedback-check"><input type="checkbox" checked={feedback.wouldRecommend} onChange={(e) => setFeedback({ ...feedback, wouldRecommend: e.target.checked })} /> Would recommend SetuStock to another distributor</label><button type="submit" disabled={busy}>Save client feedback</button></form></div>}
    </article>
    <div className="wizard-actions">{step > 0 && <button className="secondary-btn" onClick={() => setStep(step - 1)}>Back</button>}<button onClick={saveStep} disabled={busy}>{busy ? 'Saving...' : step === steps.length - 1 ? 'Complete onboarding' : 'Save & continue'}</button></div>
    <div className="onboarding-note"><strong>Implementation tip</strong><p>For a real client, import approved master data and opening balances, review the validation errors, then verify the audit log before inviting staff.</p></div>
  </div>;
}
