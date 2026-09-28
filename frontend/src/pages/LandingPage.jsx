import Brand from '../components/Brand';
import Icon from '../components/Icon';

const signals = [
  ['01', 'Inventory', 'Know what is available before the phone rings.'],
  ['02', 'Order flow', 'Move from WhatsApp request to dispatch without retyping.'],
  ['03', 'Collections', 'Keep every rupee visible until it lands.'],
];

const roles = ['OWNER', 'SALES', 'WAREHOUSE', 'ACCOUNTANT'];

const plans = [
  { code: 'FREE', name: 'Free', price: '₹0', suffix: 'forever', text: 'For small teams getting their daily stock and order rhythm in place.', features: ['1 owner workspace', 'Products and inventory', 'Up to 50 SKUs', 'Dashboard and basic reports'], details: ['Role-aware overview', 'Customer and order records', 'Demo-safe workspace data'], tone: 'free' },
  { code: 'PREMIUM', name: 'Premium', price: '₹2,499', suffix: '/ month', text: 'For growing distributors who need connected sales, stock and collections.', features: ['Everything in Free', 'WhatsApp order drafts', 'GST invoices and collections', 'Field sales and approvals'], details: ['Up to 10 users', 'Up to 5 warehouses', 'Customer portal, delivery and forecasting'], tone: 'premium' },
  { code: 'ENTERPRISE', name: 'Enterprise', price: 'Custom', suffix: 'for your network', text: 'For multi-branch operations that need controls, integrations and support.', features: ['Everything in Premium', 'Multi-branch permissions', 'Advanced WMS and analytics', 'API, audit and security controls'], details: ['Unlimited operating perspectives', 'Integration and onboarding support', 'Custom approval and compliance workflows'], tone: 'enterprise' },
];

export default function LandingPage({ navigate }) {
  return (
    <div className="landing-v2">
      <header className="landing-v2-nav">
        <Brand />
        <nav aria-label="Primary navigation">
          <a href="#features">Capabilities</a>
          <a href="#workflow">Daily loop</a>
          <a href="#roles">For your team</a>
          <a href="#plans">Plans</a>
        </nav>
        <div className="v2-nav-actions">
          <span className="v2-live-status"><i /> NCR / 2026</span>
          <button className="v2-btn v2-btn-ghost v2-btn-register" onClick={() => navigate('/login?view=register')}>Create account</button>
          <button className="v2-btn v2-btn-ghost" onClick={() => navigate('/login')}>Log in <Icon name="arrow" size={15} /></button>
        </div>
      </header>

      <main>
        <section className="v2-hero">
          <div className="v2-hero-copy">
            <div className="v2-kicker"><span>SetuStock / 01</span><b>Wholesale operations OS</b></div>
            <h1>Stock moves fast. Your system should move faster.</h1>
            <p className="v2-hero-sub">A field-built command layer for NCR wholesalers and distributors: inventory, B2B orders, credit and dispatch in one clear rhythm.</p>
            <div className="v2-hero-actions">
              <button className="v2-btn v2-btn-primary" onClick={() => navigate('/login')}>Enter the workspace <Icon name="arrow" size={17} /></button>
              <button className="v2-text-btn" onClick={() => navigate('/portal')}>Open dealer portal <span>↗</span></button>
            </div>
            <div className="v2-proof-row">
              <span><b>5</b> operating roles</span>
              <span><b>24/7</b> stock visibility</span>
              <span><b>GST</b> ready records</span>
            </div>
          </div>

          <div className="v2-hero-stage" aria-label="SetuStock operations preview">
            <div className="v2-stage-grid" />
            <div className="v2-stage-top"><span>LIVE OPERATIONS</span><strong>09:42 <i /></strong></div>
            <div className="v2-stage-main">
              <div className="v2-stage-heading"><div><small>Good afternoon, Arjun</small><h2>Today’s control room</h2></div><span className="v2-avatar">AK</span></div>
              <div className="v2-stage-metrics">
                <div className="v2-stage-metric v2-metric-accent"><small>Sales today</small><strong>₹1,84,240</strong><em>+12.4%</em></div>
                <div className="v2-stage-metric"><small>Receivable</small><strong>₹4.72L</strong><em>18 accounts</em></div>
                <div className="v2-stage-metric"><small>Dispatch queue</small><strong>07</strong><em>ready to move</em></div>
              </div>
              <div className="v2-stage-body">
                <div className="v2-chart"><div className="v2-chart-head"><span>Sales pulse</span><b>THIS WEEK</b></div><div className="v2-bars"><i /><i /><i /><i /><i /><i /><i /></div><div className="v2-chart-labels"><span>M</span><span>T</span><span>W</span><span>T</span><span>F</span><span>S</span><span>S</span></div></div>
                <div className="v2-attention"><div className="v2-chart-head"><span>Needs attention</span><b>03 ITEMS</b></div><div><i className="amber" /><span><strong>Polycab 2.5mm</strong><small>7 coils left</small></span><b>LOW</b></div><div><i className="rose" /><span><strong>Metro Electricals</strong><small>₹38,400 overdue</small></span><b>12D</b></div><div><i className="mint" /><span><strong>SO-1094 ready</strong><small>R.K. Trading Co.</small></span><b>GO</b></div></div>
              </div>
            </div>
            <div className="v2-float-card v2-float-left"><span>STOCK COVER</span><strong>18.4 <small>days</small></strong><i><b /></i><em>Healthy across 3 warehouses</em></div>
            <div className="v2-float-card v2-float-right"><span>FIELD TEAM</span><strong>12 <small>visits today</small></strong><div className="v2-avatars"><i>RS</i><i>MK</i><i>+4</i></div></div>
          </div>
        </section>

        <div className="v2-marquee"><span>BUILT FOR THE EVERYDAY PRESSURE OF WHOLESALE</span><i>✦</i><span>STOCK · CREDIT · DISPATCH · PAYMENT</span><i>✦</i><span>DELHI NCR / INDIA</span></div>

        <section className="v2-section v2-capabilities" id="features">
          <div className="v2-section-intro"><div className="v2-kicker"><span>SetuStock / 02</span><b>One connected operating layer</b></div><h2>Not another dashboard. A better daily rhythm.</h2><p>The work is messy. The system should make the next action obvious.</p></div>
          <div className="v2-signal-grid">{signals.map(([no, title, text]) => <article key={no} className={`v2-signal-card signal-${no}`}><span>{no}</span><Icon name={title === 'Inventory' ? 'box' : title === 'Order flow' ? 'receipt' : 'chart'} size={22} /><h3>{title}</h3><p>{text}</p><b className="v2-card-arrow">↗</b></article>)}</div>
        </section>

        <section className="v2-section v2-workflow" id="workflow">
          <div className="v2-workflow-copy"><div className="v2-kicker"><span>SetuStock / 03</span><b>The daily loop</b></div><h2>From enquiry to cash, without losing the thread.</h2><p>Every handoff has a place. Every exception has a signal. Your team spends less time asking “what happened?” and more time moving the business.</p><button className="v2-text-btn" onClick={() => navigate('/login')}>See the workspace <span>↗</span></button></div>
          <div className="v2-loop"><div className="v2-loop-line" />{['Customer enquiry', 'Price + availability', 'Reserve & pack', 'Dispatch goods', 'Collect payment'].map((step, i) => <div className="v2-loop-step" key={step}><span>0{i + 1}</span><strong>{step}</strong><small>{['WhatsApp, phone, counter', 'Customer-specific rules', 'Warehouse-ready queue', 'Proof and status trail', 'Ledger stays current'][i]}</small></div>)}</div>
        </section>

        <section className="v2-section v2-roles" id="roles"><div className="v2-roles-head"><div><div className="v2-kicker"><span>SetuStock / 04</span><b>One system / many perspectives</b></div><h2>Give every person the right window.</h2></div><p>Owner, manager, sales, warehouse and accountant see the same business from the angle they need.</p></div><div className="v2-role-strip">{roles.map((role, i) => <div key={role} className={i === 0 ? 'active' : ''}><span>0{i + 1}</span><strong>{role}</strong><small>{['See the whole machine', 'Keep the pipeline moving', 'Make stock real', 'Keep cash clean'][i]}</small></div>)}</div></section>

        <section className="v2-section v2-pricing" id="plans">
          <div className="v2-pricing-head"><div><div className="v2-kicker"><span>SetuStock / 05</span><b>Simple plans, clear upgrades</b></div><h2>Start free. Grow when the operation does.</h2></div><p>Explore the workspace before you commit. Every plan is built around the same role-aware operating layer.</p></div>
          <div className="v2-plan-grid">{plans.map((plan) => <article className={`v2-plan-card ${plan.tone} ${plan.tone === 'premium' ? 'featured' : ''}`} key={plan.code}>{plan.tone === 'premium' && <span className="v2-plan-badge">Most popular</span>}<span className="v2-plan-code">{plan.code}</span><h3>{plan.name}</h3><p>{plan.text}</p><div className="v2-plan-price"><strong>{plan.price}</strong><small>{plan.suffix}</small></div><ul>{plan.features.map((feature) => <li key={feature}>✓ {feature}</li>)}</ul><details><summary>View feature details</summary><div>{plan.details.map((detail) => <span key={detail}>{detail}</span>)}</div></details><button className={plan.tone === 'premium' ? 'v2-btn v2-btn-primary' : 'v2-btn v2-btn-ghost'} onClick={() => navigate('/login?view=register')}>{plan.tone === 'enterprise' ? 'Discuss your setup' : plan.tone === 'premium' ? 'Start premium trial' : 'Create free account'} <Icon name="arrow" size={15} /></button></article>)}</div>
          <small className="v2-pricing-note">No payment required for the Free plan. Premium and Enterprise access can be enabled from the workspace subscription screen.</small>
        </section>

        <section className="v2-cta"><div><span className="v2-kicker"><span>SetuStock / 06</span><b>Ready when you are</b></span><h2>Make the next order easier than the last one.</h2></div><button className="v2-btn v2-btn-light" onClick={() => navigate('/login?view=register')}>Open the workspace <Icon name="arrow" size={17} /></button></section>
      </main>

      <footer className="v2-footer"><Brand /><span>Wholesale operations software for the real pace of Indian distribution.</span><small>© 2026 SetuStock NCR</small></footer>
    </div>
  );
}
