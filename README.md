# SetuStock NCR

SetuStock is a multi-tenant wholesale and distribution operations platform for Indian B2B businesses. It connects inventory, customer credit, quotations, orders, GST invoices, payments, delivery, WhatsApp workflows and role-based workspaces in one application.

## What is included

- React + Vite web application
- Django JSON API with SQLite development and PostgreSQL production support
- Expo mobile client for staff and dealer workflows
- Docker Compose stack with PostgreSQL, Gunicorn and Nginx
- Playwright browser tests and Django regression tests
- Owner, Manager, Sales, Warehouse and Accountant roles
- Company, branch, warehouse and tenant-scoped records
- Products, inventory, barcode, transfers, customers, suppliers and purchasing
- Quotations, orders, stock reservation, dispatch, invoices, payments and ledgers
- GST notes, CSV import/export, audit logs, notifications, search and attachments
- Onboarding, subscription plans, billing checkout, renewals and payment retry
- Signed WhatsApp order webhooks and reviewable order drafts
- GPS delivery tracking, ETA, public tracking links, OTP and e-POD proof
- Demand forecasting and approval-ready AI reorder drafts
- Offline/PWA queue, dealer portal and mobile ordering
- Operations control center, readiness checks and backup scripts
- Guided client onboarding, CSV/XLSX migration preview, validation, rollback and feedback capture

External payment, Meta WhatsApp, GST, accounting, map and storage providers require client credentials and staging validation.

## Repository structure

```text
backend/                 Django project, API, models, migrations and tests
frontend/                React/Vite web app and Playwright tests
mobile/                  Expo React Native staff/dealer app
scripts/                 Health check and PostgreSQL backup/restore scripts
.github/workflows/       Backend, frontend, E2E and mobile CI
docker-compose.yml       PostgreSQL + Django + Nginx stack
```

Canonical project documents: [growth and product summary](GROWTH.md), [validation and operations guide](VALIDATION.md), and the [feature-wise implementation plan](FEATURES.md).

## Requirements

- Python 3.13+
- Node.js 22+
- npm and Git
- PostgreSQL for production, or Docker Desktop for the complete stack

## Quick start: frontend demo

Demo mode works without Django and uses only bundled sample data.

### Windows PowerShell

```powershell
cd frontend
npm install
Copy-Item .env.example .env
npm run dev
```

### macOS/Linux

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Open `http://localhost:5173`.

```env
VITE_APP_MODE=demo
VITE_DEMO_FALLBACK=true
```

All staff demo accounts use password `demo123`:

```text
owner@setustock.demo
manager@setustock.demo
sales@setustock.demo
warehouse@setustock.demo
accountant@setustock.demo
```

Other demo surfaces:

```text
Dealer portal:   /portal                 dealer@setustock.demo / 1234
Supplier portal: /supplier-portal        supplier@setustock.demo / 1234
Payment page:    /pay/demo-rk-payment-link
```

## Quick start: Django API

### Windows PowerShell

```powershell
cd backend
python -m venv .venv
& .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

### macOS/Linux

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

API base URL: `http://127.0.0.1:8000/api/`.

```text
GET /api/health/   liveness
GET /api/ready/    database and migration readiness
```

For live API mode, set `frontend/.env` to:

```env
VITE_APP_MODE=production
VITE_API_URL=http://127.0.0.1:8000/api
VITE_DEMO_FALLBACK=false
```

Production mode reports API failures instead of silently showing demo accounting data.

## Quick start: Docker

From the repository root:

```bash
docker compose up --build
```

```text
Frontend: http://localhost:8080
Backend:  http://localhost:8000/api/health/
Ready:    http://localhost:8000/api/ready/
```

For deployment, replace local defaults with strong secret-managed values:

```bash
DJANGO_SECRET_KEY="use-a-long-random-secret"
DB_PASSWORD="use-a-strong-database-password"
RELEASE_VERSION="2026.09.29"
VITE_API_URL="https://api.yourdomain.com/api"
docker compose up --build -d
```

The frontend API URL is compiled into the static bundle. When sharing the Docker deployment with users on other computers, always set `VITE_API_URL` to the public HTTPS API URL or expose the API through the same public domain. A localhost API URL only works on the machine running Docker.

Never run `seed_demo` against a client's production database.

## Roles and access

| Role | Main responsibility |
| --- | --- |
| Owner | Full visibility, settings, billing, security and approvals |
| Manager | Sales, inventory, purchasing, approvals and team operations |
| Sales | Customers, quotations, orders, collections, WhatsApp and field visits |
| Warehouse | Products, stock, barcode, purchasing, fulfilment and delivery |
| Accountant | Invoices, payments, ledgers, GST, reports and reconciliation |

Role permissions and subscription plan restrictions are validated by the backend as well as the frontend sidebar.

## Recommended client-demo workflow

1. Sign in as Owner and review the dashboard.
2. Configure company, branch, warehouse and team roles.
3. Create/import products, customers and suppliers.
4. Create and approve a purchase order, then receive it through GRN.
5. Create a quotation and convert it into a sales order.
6. Confirm the order and verify reserved stock.
7. Pack, mark ready and dispatch the order.
8. Create the GST invoice and verify customer outstanding.
9. Record payment and verify the ledger.
10. Create a delivery run, update GPS/ETA, open the tracking link and capture OTP e-POD.
11. Open Forecasting and create reorder drafts for approval.
12. Review audit logs, operations health, billing state and role access.

## WhatsApp setup

Keep Meta credentials on the backend in `backend/.env`:

```env
WHATSAPP_ACCESS_TOKEN=
WHATSAPP_PHONE_NUMBER_ID=
WHATSAPP_VERIFY_TOKEN=
WHATSAPP_APP_SECRET=
```

Webhook endpoint: `/api/whatsapp/webhook/`.

Inbound messages are matched to the company phone number and customer phone number, converted into reviewable order drafts and protected against duplicate provider replay. Test signed webhooks in staging before enabling live outbound delivery.

## Billing setup

The subscription workspace supports Free, Premium and Enterprise plans, usage limits, checkout records, renewals, failed-payment retries, invoices and cancellation scheduling.

Live collection requires provider credentials and a signed webhook secret. A paid plan activates only after the payment provider confirms the transaction. Never expose provider secret keys in the frontend.

## Mobile app

The Expo client supports staff login, dealer login, customer-specific catalogue/order flows, delivery visibility, offline queue support and the business assistant.

```bash
cd mobile
npm install
npx expo install --fix
```

Use a reachable LAN or HTTPS API address; a phone cannot use the computer's `127.0.0.1`:

```bash
EXPO_PUBLIC_API_URL=http://YOUR-LAN-IP:8000/api npm start
```

Dealer demo access is `dealer@setustock.demo / 1234`. Production mobile release also requires HTTPS, EAS builds, secure secrets, push notifications, crash monitoring, privacy disclosures and device testing.

## Testing

The complete validation, CI, deployment-readiness, and client-acceptance workflow is maintained in [VALIDATION.md](VALIDATION.md).

Backend:

```bash
cd backend
python manage.py check
python manage.py check --deploy
python manage.py makemigrations --check --dry-run
python manage.py test
```

Frontend:

```bash
cd frontend
npm install
npm run build
npm run test:e2e
```

Mobile configuration:

```bash
cd mobile
npm install
npx expo config --type public
```

The browser suite covers login, role restrictions, core navigation and blank-page regression checks.

## Production checklist

1. Use PostgreSQL and a unique secret-managed `DJANGO_SECRET_KEY`.
2. Set `DJANGO_DEBUG=false`, explicit allowed hosts, CORS and CSRF origins.
3. Terminate HTTPS at the reverse proxy and enable secure cookies/HSTS.
4. Build React with `VITE_APP_MODE=production` and `VITE_DEMO_FALLBACK=false`.
5. Configure SMTP for password reset and account notifications.
6. Use private object storage for uploaded documents at scale.
7. Schedule PostgreSQL backups and test a restore.
8. Monitor `/api/health/`, `/api/ready/`, 5xx responses, failed jobs, webhook retries and login lockouts.
9. Configure payment, WhatsApp, GST, accounting and map providers in staging first.
10. Create the client's own owner/company/branch/warehouse records; do not use public demo accounts.

Backup commands:

```bash
./scripts/backup_postgres.sh
./scripts/restore_postgres.sh backups/<file>.dump
./scripts/healthcheck.sh http://localhost:8000/api/ready/
```

Backups include SHA-256 sidecar files. Set `BACKUP_RETENTION_DAYS` to prune old backup files.

## Known boundaries

- GST/e-invoice/e-way-bill screens are provider-ready, not statutory certification.
- Billing is provider-ready until real credentials and webhooks are configured.
- The generic commerce/channel adapter is not a certified live ONDC integration.
- AI suggestions create drafts or approval proposals; financial/customer-facing actions require human approval.
- Demo mode uses sample data and must not be used for real accounting or GST filing.

## Recommended next features

After the current release, prioritize:

1. **Live payment reconciliation** — settlements, refunds, partial payments and automatic invoice allocation.
2. **Real WhatsApp production inbox** — templates, media/voice-note ingestion, delivery receipts, opt-in management and retry queues.
3. **Driver mobile e-POD capture** — native camera signature/photo capture, push notifications, route maps and background location updates.
4. **Operational observability** — APM/error tracking, centralized logs, alert routing, backup-age alerts and tenant usage analytics.
5. **AI feedback and action governance** — forecast accuracy tracking, recommendation outcomes, approval limits and safe execution of approved collection/transfer actions.

## Compliance note

SetuStock provides operational and GST-oriented workflows, but it is not a certified GST filing or accounting product by itself. Validate the client's legal, tax, privacy, payment and data-retention requirements before production use.
