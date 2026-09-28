import { useEffect, useMemo, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { createApiResource, getApiResource } from '../services/api';
import { demoForecasts } from '../data/growthData';

const money = (value) => `₹${Number(value || 0).toLocaleString('en-IN', { maximumFractionDigits: 0 })}`;

export default function AIForecastingPage() {
  const { mode } = useAuth();
  const [horizon, setHorizon] = useState(30);
  const [forecasts, setForecasts] = useState(demoForecasts);
  const [notice, setNotice] = useState('');
  const [busy, setBusy] = useState(false);
  const [generatedAt, setGeneratedAt] = useState(null);
  const load = async () => {
    if (mode !== 'api') { setForecasts(demoForecasts); return; }
    try { const result = await getApiResource('forecasting', `horizon=${horizon}`); setForecasts(result.forecasts || []); } catch (error) { setNotice(error.message); }
  };
  useEffect(() => { load(); }, [mode, horizon]);
  const generate = async () => { setBusy(true); try { if (mode === 'api') await createApiResource('forecasting', { horizon }); setGeneratedAt(new Date()); setNotice(`${horizon}-day forecast regenerated from company demand.`); await load(); } catch (error) { setNotice(error.message); } finally { setBusy(false); } };
  const createPlan = async () => { setBusy(true); try { if (mode === 'api') await createApiResource('supply-planning', { action: 'generate', horizon, name: `AI ${horizon}-day replenishment plan` }); setNotice('Replenishment plan generated and ready for approval.'); } catch (error) { setNotice(error.message); } finally { setBusy(false); } };
  const summary = useMemo(() => ({ products: forecasts.length, purchase: forecasts.reduce((total, row) => total + Number(row.recommendedPurchase || 0), 0), atRisk: forecasts.filter(row => Number(row.recommendedPurchase || 0) > 0).length, confidence: forecasts.length ? Math.round(forecasts.reduce((total, row) => total + Number(row.confidence || 0), 0) / forecasts.length) : 0 }), [forecasts]);
  return <div className="forecasting-workspace">
    {notice && <div className="inline-notice">{notice}<button onClick={() => setNotice('')}>×</button></div>}
    <div className="module-header"><div><span className="eyebrow">AI demand planning</span><h1>Forecasting control room</h1><p>Turn recent demand, trend, safety stock and inventory into explainable replenishment decisions.</p></div><div className="forecast-actions"><label>Planning horizon<select value={horizon} onChange={e => setHorizon(Number(e.target.value))}><option value={14}>14 days</option><option value={30}>30 days</option><option value={60}>60 days</option><option value={90}>90 days</option></select></label><button onClick={generate} disabled={busy}>{busy ? 'Working…' : 'Regenerate forecast'}</button><button className="secondary-btn" onClick={createPlan} disabled={busy}>Create replenishment plan</button></div></div>
    <div className="forecast-summary"><article><span>SKUs modelled</span><strong>{summary.products}</strong><small>live company catalogue</small></article><article><span>Recommended purchase</span><strong>{summary.purchase.toLocaleString('en-IN')}</strong><small>units across SKUs</small></article><article><span>Needs action</span><strong>{summary.atRisk}</strong><small>positive replenishment quantity</small></article><article><span>Average confidence</span><strong>{summary.confidence}%</strong><small>model confidence</small></article></div>
    <article className="panel module-panel forecast-table-panel"><div className="panel-head"><div><span>Explainable recommendations</span><h3>{horizon}-day demand outlook</h3></div><small>{generatedAt ? `Updated ${generatedAt.toLocaleTimeString('en-IN')}` : 'Regenerate to refresh the planning snapshot'}</small></div><div className="table-wrap"><table className="data-table module-table"><thead><tr><th>Product</th><th>Stock</th><th>Daily demand</th><th>Trend</th><th>Forecast</th><th>Safety</th><th>Recommended buy</th><th>Confidence</th></tr></thead><tbody>{forecasts.map((row, index) => <tr key={row.sku || row.id || index}><td><strong>{row.product}</strong><small>{row.sku} · {row.warehouse || 'All warehouses'}</small></td><td>{row.currentStock}</td><td>{Number(row.avgDaily || 0).toFixed(1)}</td><td className={Number(row.trend) >= 0 ? 'trend-up' : 'trend-down'}>{Number(row.trend || 0) >= 0 ? '+' : ''}{Number(row.trend || 0).toFixed(1)}%</td><td>{Math.round(row.forecast || 0)}</td><td>{Math.round(row.safetyStock || 0)}</td><td><strong>{Math.round(row.recommendedPurchase || 0)}</strong><small>{Number(row.recommendedPurchase || 0) > 0 ? 'replenishment needed' : 'stock covered'}</small></td><td><span className="confidence-meter"><i style={{ width: `${Math.min(100, Number(row.confidence || 0))}%` }} />{Math.round(row.confidence || 0)}%</span></td></tr>)}</tbody></table></div></article>
  </div>;
}
