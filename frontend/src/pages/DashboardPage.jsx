import { useAuth } from '../context/AuthContext';
import { demoDashboard, roleHomeCopy } from '../data/demoData';
import StatCard from '../components/StatCard';

const money = (value) => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(value);

const roleMetrics = {
  OWNER: ['salesToday', 'receivable', 'stockValue', 'openOrders'],
  MANAGER: ['salesToday', 'openOrders', 'lowStock', 'receivable'],
  SALES: ['salesToday', 'openOrders', 'receivable'],
  WAREHOUSE: ['openOrders', 'lowStock', 'stockValue'],
  ACCOUNTANT: ['receivable', 'salesToday', 'salesMonth'],
};

const meta = {
  salesToday: ['Sales today', (v) => money(v), '12.4% above yesterday', 'success'],
  salesMonth: ['Month sales', (v) => money(v), 'September running total', 'neutral'],
  receivable: ['Receivable', (v) => money(v), 'Across active credit customers', 'warning'],
  stockValue: ['Stock value', (v) => money(v), 'At current purchase cost', 'neutral'],
  openOrders: ['Open orders', (v) => String(v), '7 waiting for dispatch', 'info'],
  lowStock: ['Low stock SKUs', (v) => String(v), 'Needs purchase attention', 'warning'],
};

export default function DashboardPage() {
  const { user } = useAuth();
  const data = demoDashboard;
  const keys = roleMetrics[user.role] || roleMetrics.OWNER;

  return (
    <div className="dashboard-page">
      <div className="page-intro">
        <div><span className="section-kicker">{user.role} workspace</span><h1>Good afternoon, {user.name.split(' ')[0]}.</h1><p>{roleHomeCopy[user.role]}</p></div>
        <div className="date-chip"><span>21</span><div><strong>September</strong><small>Monday · Delhi NCR</small></div></div>
      </div>

      <section className="stats-grid">
        {keys.map((key) => {
          const [label, formatter, hint, tone] = meta[key];
          return <StatCard key={key} label={label} value={formatter(data.metrics[key])} hint={hint} tone={tone} />;
        })}
      </section>

      <section className="dashboard-grid">
        <article className="panel orders-panel">
          <div className="panel-head"><div><span>Sales queue</span><h3>Recent orders</h3></div><button>View orders</button></div>
          <div className="table-wrap">
            <table className="data-table">
              <thead><tr><th>Order</th><th>Customer</th><th>Total</th><th>Payment</th><th>Status</th></tr></thead>
              <tbody>
                {data.recentOrders.map((order) => <tr key={order.id}><td><strong>{order.id}</strong><small>{order.date}</small></td><td>{order.customer}</td><td>{money(order.total)}</td><td><span className={`text-status ${order.payment.toLowerCase()}`}>{order.payment}</span></td><td><span className={`status-pill ${order.status.toLowerCase()}`}>{order.status}</span></td></tr>)}
              </tbody>
            </table>
          </div>
        </article>

        <article className="panel activity-panel">
          <div className="panel-head"><div><span>Exceptions</span><h3>Needs attention</h3></div></div>
          <div className="activity-list">
            {data.activity.map((item) => <div className="activity-item" key={item.text}><i className={item.tone} /><div><strong>{item.title}</strong><p>{item.text}</p><small>{item.time}</small></div></div>)}
          </div>
          <div className="mini-ledger"><div><span>Collection due this week</span><strong>₹1.38L</strong></div><div className="ledger-bar"><i /></div><small>62% of weekly receivables already collected</small></div>
        </article>
      </section>
    </div>
  );
}
