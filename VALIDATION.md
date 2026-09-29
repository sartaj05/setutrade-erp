# SetuStock validation and operations guide

This is the single source of truth for local checks, CI gates, deployment readiness, client acceptance, and demo handoff.

## Validation commands

Run backend checks from `backend`:

```bash
python manage.py check
python manage.py check --deploy
python manage.py makemigrations --check --dry-run
python manage.py test
```

Run the client acceptance regression suite:

```bash
python manage.py test api.tests.ProductionApiTests
```

Run frontend checks from `frontend`:

```bash
npm install
npm run build
npm run test:e2e
```

Validate the mobile configuration from `mobile`:

```bash
npm install
npx expo config --type public
```

The acceptance path covers login, role context, customer, quotation, order, stock reservation, invoice, UPI payment, delivery OTP/e-POD, ledger, and a sidebar API smoke test. The browser suite covers login, role restrictions, core navigation, and blank-page regressions.

The onboarding acceptance path additionally covers company settings, branch/warehouse setup, team invitation, CSV/XLSX preview and column mapping, required-field/GST/price validation, duplicate detection, approved import commit, rollback, import history, and client feedback submission.

Onboarding data endpoints are company-scoped and role-guarded:

```text
/api/onboarding/
/api/onboarding/feedback/
/api/imports/
/api/imports/preview/
/api/imports/<id>/commit/
/api/imports/<id>/rollback/
```

## GitHub CI gate

`.github/workflows/ci.yml` is the authoritative connected-environment validation. It installs dependencies and runs Django checks, deployment checks, migration checks, migrations, demo seeding, backend tests, the Vite production build, Playwright E2E tests, and Expo configuration validation on pushes and pull requests.

Before client go-live, require a green CI run. Also run `git diff --check` and confirm there are no merge-conflict markers in tracked source files.

## Recorded package checks

The packaging environment previously confirmed Python compilation, JavaScript/JSX parsing, migration continuity through `0056`, Growth v5 model coverage in migrations `0043`-`0052`, the later `0053`-`0056` follow-up migrations, registered Growth v5 API routes, Git whitespace checks, and a clean working tree before packaging. It did not have registry access for fresh Django/npm installs, so CI remains the final runtime/build authority.

## Deployment modes

### Frontend demo

Use a static host with `frontend` as the root, `npm run build` as the build command, and `dist` as the output. Use:

```env
VITE_APP_MODE=demo
VITE_DEMO_FALLBACK=true
VITE_API_URL=https://unused.example/api
```

This mode uses sample data only and must not receive real customer, accounting, payment, or GST data.

### Production

Use React behind HTTPS, Django/Gunicorn, PostgreSQL, and private or signed object storage for uploaded documents. Set `DJANGO_DEBUG=false`, explicit allowed hosts, CORS/CSRF origins, a secret-managed `DJANGO_SECRET_KEY`, secure cookies/HTTPS settings, SMTP, backups, monitoring, and:

```env
VITE_APP_MODE=production
VITE_DEMO_FALLBACK=false
```

Run migrations, collect static files, `python manage.py check --deploy`, and a health/readiness probe before traffic is enabled. Never run `seed_demo` against a client database.

Docker Compose exposes the frontend on port 8080 and Django health/readiness endpoints on port 8000. The local Compose profile intentionally allows local HTTP; production requires an HTTPS reverse proxy.

## Client acceptance checklist

1. Sign in as Owner and verify company, GST, bank, and settings.
2. Create a branch, warehouse, team user, and role assignments.
3. Import or create products, customers, and suppliers.
4. Create and approve a purchase order, receive it through GRN, and verify stock increases.
5. Create a quotation and convert it into a sales order.
6. Confirm the order and verify reserved stock.
7. Pack, mark ready, dispatch, and verify stock decreases.
8. Create the GST invoice and verify customer ledger/outstanding.
9. Record a customer payment and verify receivables reduce.
10. Transfer stock between warehouses and verify both locations.
11. Process a return or adjustment and review the audit log.
12. Create a delivery run, update GPS/ETA, open tracking, and capture OTP/e-POD.
13. Open forecasting and create reorder drafts for approval.
14. Review reports, notifications, search, attachments, billing state, operations health, and role access.

## Go-live safeguards

- Create the client's own owner, company, branch, and warehouse records; do not use public demo accounts.
- Configure and stage-test payment/bank, WhatsApp, GST, accounting, maps, storage, SMTP, and monitoring providers.
- Schedule PostgreSQL/media backups and perform a restore test.
- Monitor `/api/health/`, `/api/ready/`, 5xx rates, failed jobs, webhook retries, login lockouts, disk usage, and backup age.
- Document domain, database, vendor credential ownership, escalation contacts, and the restore procedure.
- Validate legal, tax, privacy, payment, retention, and statutory integration requirements with the client's advisers.

Useful operational scripts:

```bash
./scripts/backup_postgres.sh
./scripts/restore_postgres.sh backups/<file>.dump
./scripts/healthcheck.sh http://localhost:8000/api/ready/
```
