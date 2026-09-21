# SetuStock NCR

A demo-ready B2B wholesale/distribution management SaaS starter aimed at Delhi NCR wholesalers and distributors.

## Stack
- Frontend: React 19 + Vite 8 + plain CSS
- Backend: core Django 6 APIs using `JsonResponse` and Django signing, no DRF
- Database: SQLite for local/demo use, PostgreSQL-ready through environment variables
- Deployment: frontend-only demo supported, or React + Django API

## Product modules
- Role based access: `OWNER`, `MANAGER`, `SALES`, `WAREHOUSE`, `ACCOUNTANT`
- Dashboard
- Products and base inventory
- Customers, credit and B2B orders
- GST invoices
- Suppliers, purchase orders and GRN
- Customer credit ledger and ageing
- Multi-warehouse inventory and transfers
- Barcode/QR workflow
- WhatsApp B2B draft ordering
- GST/HSN, credit/debit notes and e-invoice-ready fields
- Customer price lists, quantity slabs and schemes
- Sales/purchase returns and stock adjustments
- Field-sales visits, collections and targets
- Smart reorder suggestions and business insights
- Quotations/payments/reports/team/settings starter surfaces
- Public landing page + login
- Automatic frontend demo-data fallback when Django is unavailable

See `FEATURES.md` for feature details and `COMMIT_PLAN.md` for the feature-wise Git history.

## Demo accounts
Password for every demo account: `demo123`

```text
owner@setustock.demo
manager@setustock.demo
sales@setustock.demo
warehouse@setustock.demo
accountant@setustock.demo
```

## Run frontend

```bash
cd frontend
npm install
npm run dev
```

The demo works without the backend. Leave `VITE_DEMO_FALLBACK=true` to allow local demo login when the API is unreachable.

## Run backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

## Environment
Copy `frontend/.env.example` to `frontend/.env` and `backend/.env.example` to `backend/.env`.

The frontend tries the Django API first. If the API is unavailable, it falls back to its bundled demo accounts/data unless `VITE_DEMO_FALLBACK=false`.

## Validate

Backend:

```bash
cd backend
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

Frontend:

```bash
cd frontend
npm install
npm run build
```

## Git / GitHub
The downloadable project contains `.git` and the complete feature-wise history.

```bash
git log --oneline --reverse
```

A GitHub Actions CI workflow is included. See `GITHUB_SETUP.md` for publishing the already-initialized repository to your GitHub account.

## Deployment
- Frontend: Vercel / Netlify / Cloudflare Pages
- Backend: Render / Railway / Fly.io / VPS
- Production database: PostgreSQL

See `DEPLOYMENT.md` for environment and hardening notes.

## Production warning
This is a demo/product starter, not audited accounting software. Before storing real customer data, add company/tenant isolation, full write-operation permission checks, immutable audit logs, backups, production authentication/token rotation, verified GST/e-invoice integrations, WhatsApp credentials/webhooks, monitoring and comprehensive tests. Do not keep the public `demo123` users enabled for a real deployment.
