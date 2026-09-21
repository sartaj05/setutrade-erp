import Brand from '../components/Brand';
import Icon from '../components/Icon';

const features = [
  ['box', 'Inventory that speaks shop language', 'Live stock, low-stock signals, SKU search and warehouse-ready quantity tracking.'],
  ['receipt', 'B2B orders & GST-ready records', 'Capture phone, counter and WhatsApp orders in one clean order flow.'],
  ['users', 'Customer credit / udhaar', 'Track outstanding balances, payment history and follow-up priority without ledger archaeology.'],
  ['message', 'WhatsApp-first workflow', 'Share order summaries, payment reminders and product enquiries using the channel customers already use.'],
  ['chart', 'Owner-level visibility', 'Sales, receivables, stock value and order health in a calm dashboard built for quick decisions.'],
  ['shield', 'Role-based control', 'Owner, manager, sales, warehouse and accountant views keep sensitive actions where they belong.'],
];

const trustItems = ['Role-based access', 'Demo works without backend', 'Mobile-first responsive UI', 'Django API ready'];

export default function LandingPage({ navigate }) {
  return (
    <div className="marketing-shell">
      <header className="marketing-nav container">
        <Brand />
        <nav className="nav-links" aria-label="Primary navigation">
          <a href="#features">Features</a>
          <a href="#roles">Roles</a>
          <a href="#workflow">Workflow</a>
        </nav>
        <button className="btn btn-secondary nav-login" onClick={() => navigate('/login')}>Log in</button>
      </header>

      <main>
        <section className="hero container">
          <div className="hero-copy">
            <div className="eyebrow"><span className="live-dot" /> Built for NCR wholesalers & distributors</div>
            <h1>Run stock, B2B orders and customer credit without running between five apps.</h1>
            <p className="hero-sub">SetuStock keeps inventory, orders, receivables and WhatsApp operations connected in one dependable workspace for growing trading businesses.</p>
            <div className="hero-actions">
              <button className="btn btn-primary" onClick={() => navigate('/login')}>Open demo <Icon name="arrow" size={17} /></button>
              <a className="text-link" href="#features">See what it manages</a>
            </div>
            <div className="trust-row">
              {trustItems.map((item) => <span key={item}><Icon name="check" size={15} /> {item}</span>)}
            </div>
          </div>

          <div className="hero-board" aria-label="SetuStock product preview">
            <div className="board-top">
              <div><small>Today’s pulse</small><strong>Good afternoon, Arjun</strong></div>
              <div className="mini-avatar">AK</div>
            </div>
            <div className="metric-grid">
              <div className="metric-card featured"><small>Sales today</small><strong>₹1,84,240</strong><span>↑ 12.4% vs yesterday</span></div>
              <div className="metric-card"><small>Receivable</small><strong>₹4.72L</strong><span>18 customers</span></div>
              <div className="metric-card"><small>Orders</small><strong>34</strong><span>7 pending dispatch</span></div>
            </div>
            <div className="board-section">
              <div className="board-heading"><strong>Needs attention</strong><span>View all</span></div>
              <div className="attention-row"><i className="status-dot amber"/><div><strong>Polycab 2.5mm wire</strong><small>Only 7 coils left</small></div><span>Low stock</span></div>
              <div className="attention-row"><i className="status-dot rose"/><div><strong>Metro Electricals</strong><small>₹38,400 overdue</small></div><span>12 days</span></div>
              <div className="attention-row"><i className="status-dot sage"/><div><strong>SO-1094 ready</strong><small>R.K. Trading Co.</small></div><span>Dispatch</span></div>
            </div>
          </div>
        </section>

        <section className="soft-band" id="features">
          <div className="container section-wrap">
            <div className="section-heading">
              <span className="section-kicker">One operating layer</span>
              <h2>Built around the messy parts of wholesale business.</h2>
              <p>Not another generic CRM wearing an inventory hat. The workflow starts with stock, orders, customer balances and fulfilment.</p>
            </div>
            <div className="feature-grid">
              {features.map(([icon, title, desc]) => (
                <article className="feature-card" key={title}>
                  <div className="feature-icon"><Icon name={icon} /></div>
                  <h3>{title}</h3>
                  <p>{desc}</p>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section className="container role-section" id="roles">
          <div className="section-heading left">
            <span className="section-kicker">Role-aware by default</span>
            <h2>Everyone sees the work they actually need.</h2>
          </div>
          <div className="role-strip">
            {[
              ['Owner', 'All modules, financial overview, users and settings'],
              ['Manager', 'Sales, customers, inventory and operational reports'],
              ['Sales', 'Customers, orders, quotations and collection follow-ups'],
              ['Warehouse', 'Products, stock, picking and dispatch queue'],
              ['Accountant', 'Invoices, receivables, payments and reports'],
            ].map(([role, copy]) => <div className="role-card" key={role}><strong>{role}</strong><p>{copy}</p></div>)}
          </div>
        </section>

        <section className="container workflow" id="workflow">
          <div className="workflow-copy">
            <span className="section-kicker">Simple daily loop</span>
            <h2>Enquiry → order → stock → dispatch → payment.</h2>
            <p>Capture a customer request, confirm available stock, create an order, hand it to fulfilment and keep the outstanding balance visible until payment lands.</p>
          </div>
          <div className="workflow-steps">
            {['Customer enquiry', 'Create B2B order', 'Reserve stock', 'Dispatch goods', 'Track payment'].map((s, i) => <div key={s}><span>0{i + 1}</span><strong>{s}</strong></div>)}
          </div>
        </section>

        <section className="cta-section">
          <div className="container cta-card">
            <div><span className="section-kicker">Demo-ready</span><h2>See the role-based product before connecting a backend.</h2><p>The React app carries realistic local demo data and automatically uses it when Django is offline.</p></div>
            <button className="btn btn-light" onClick={() => navigate('/login')}>Enter demo <Icon name="arrow" size={17} /></button>
          </div>
        </section>
      </main>

      <footer className="container footer"><Brand /><p>Wholesale operations software concept for Delhi NCR.</p><span>© 2026 SetuStock</span></footer>
    </div>
  );
}
