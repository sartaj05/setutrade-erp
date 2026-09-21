# SetuStock NCR

SetuStock is a client-shareable wholesale/distribution operations starter for Indian B2B businesses. It combines React + Vite with core Django APIs and supports both a safe standalone demo deployment and a live API-backed production deployment.

## What is included

- Trust-first responsive landing page and login
- Roles: `OWNER`, `MANAGER`, `SALES`, `WAREHOUSE`, `ACCOUNTANT`
- Tenant hierarchy: Company → Branch → Warehouse → User
- Company-scoped products, customers, suppliers, orders, invoices and reports
- Sales orders with stock reservation, packing/readiness and dispatch stock posting
- Suppliers, purchase orders, approval, GRN and supplier payable posting
- GST invoices with CGST/SGST/IGST, HSN, credit/debit notes and print-to-PDF HTML
- Customer credit ledger, ageing, payments and supplier payments
- Multi-warehouse balances and approved transfer → dispatch → receive workflow
- Barcode/SKU lookup, stock actions, label printing and browser camera scanning where supported
- WhatsApp B2B draft parsing plus optional Meta WhatsApp live outbound adapter
- Customer-specific price lists, quantity slabs and schemes
- Sales/purchase returns, damaged stock and stock adjustments
- Field-sales visits, targets and collections
- Reorder intelligence and business reporting
- Quotations that convert to orders
- Company onboarding/branding, branches and team accounts
- Audit log, notifications, global search and file attachments
- Product/customer CSV import and operational CSV exports
- Password change/reset, expiring access + refresh sessions, revocation and login throttling
- PWA manifest/service worker for installable mobile-friendly use
- PostgreSQL-ready configuration, Docker Compose, backup/restore scripts and health checks
- GitHub Actions CI and Django workflow tests

See `FEATURES.md` for module details and `CLIENT_HANDOFF.md` for client-sharing guidance.

## Two deployment modes

### 1. Safe sales demo

The React app can run without Django. It uses bundled sample data only when explicitly built with:

```env
VITE_APP_MODE=demo
VITE_DEMO_FALLBACK=true
```

Demo password: `demo123`

```text
owner@setustock.demo
manager@setustock.demo
sales@setustock.demo
warehouse@setustock.demo
accountant@setustock.demo
```

### 2. Production/live client mode

Use:

```env
VITE_APP_MODE=production
VITE_API_URL=https://api.example.com/api
VITE_DEMO_FALLBACK=false
```

Production mode requires the Django API. It does not silently replace an API failure with sample accounting data.

## Local frontend

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

## Local backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py seed_demo  # demo/staging only
python manage.py runserver
```

## Full local production-like stack

At repository root:

```bash
export DJANGO_SECRET_KEY='replace-with-a-long-random-secret'
export DB_PASSWORD='replace-this-password'
docker compose up --build
```

Frontend: `http://localhost:8080`
Backend: `http://localhost:8000/api/health/`

The Docker frontend is built in production mode and therefore expects Django to be available.

## Validation

Backend CI performs:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py migrate --noinput
python manage.py test
```

Frontend CI performs:

```bash
npm install
npm run build
```

## Git / GitHub

The downloadable project is already an initialized Git repository with feature-wise history.

```bash
git status
git log --oneline --reverse
git branch
```

See `GITHUB_SETUP.md` before pushing it to your GitHub account.

## Important compliance note

SetuStock provides GST-oriented invoice/data workflows, but it is not a certified GST filing, e-invoice or accounting product by itself. Live GST/e-invoice/e-way-bill calls must be connected to an authorised provider and validated for the client's actual legal/compliance requirements before relying on them for statutory filing.


## Growth v2: 10 additional phases

The repository also includes a separate B2B dealer portal, delivery/e-POD, approvals, purchase invoice OCR review, accounting exports, offline/PWA sync, SaaS subscription billing, advanced forecasting, a data-grounded business assistant, and an Expo Android/iOS client. See `GROWTH_V2.md` for the feature map and production boundaries.
