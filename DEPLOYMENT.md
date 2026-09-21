# Deployment Guide

## 1. Frontend demo-only deployment
The React app can be deployed without Django. It will use its built-in demo accounts and data.

### Vercel
1. Import the repository.
2. Set **Root Directory** to `frontend`.
3. Build command: `npm run build`.
4. Output directory: `dist`.
5. Keep `VITE_DEMO_FALLBACK=true`.
6. If you do not have a backend yet, `VITE_API_URL` may point to an unavailable local/default URL; login will fall back automatically for the supplied demo accounts.

### Netlify / Cloudflare Pages
Use `frontend` as the project root, `npm run build` as the build command, and `dist` as the output directory. `_redirects` is included for SPA navigation on Netlify-compatible hosts.

## 2. Django backend deployment
The backend is a standard WSGI Django app.

Typical commands:

```bash
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
```

Set these environment variables in the backend host:

```text
DJANGO_SECRET_KEY=<strong random value>
DJANGO_DEBUG=false
DJANGO_ALLOWED_HOSTS=<your-api-domain>
CORS_ALLOWED_ORIGINS=https://<your-frontend-domain>
DB_ENGINE=django.db.backends.postgresql
DB_NAME=...
DB_USER=...
DB_PASSWORD=...
DB_HOST=...
DB_PORT=5432
```

Run `python manage.py seed_demo` once if you want the public demo users/data available.

## 3. Connect frontend to backend
Set on the frontend host:

```text
VITE_API_URL=https://<your-api-domain>/api
VITE_DEMO_FALLBACK=true
```

Redeploy the frontend. Login will use Django when the API is online. If the API has a network outage, the supplied demo accounts can still enter local demo mode.

## 4. Production hardening before real customer data
This repository is deliberately a sales/demo-ready starter, not a finished accounting product. Before storing real business data:

- Replace demo bearer-token signing with your chosen production auth/session architecture and token rotation strategy.
- Add tenant/company isolation to every operational model and query.
- Add audit logs for price, stock, credit and invoice changes.
- Add GST invoice numbering rules, tax place-of-supply logic and validated GSTIN fields for your actual compliance scope.
- Put rate limiting and stricter CORS/security headers at the reverse proxy/API layer.
- Add backups, object storage for documents, monitoring and error reporting.
- Add proper permissions to create/update/delete operations, not only read access.
- Do not keep the public `demo123` accounts enabled in a real customer deployment.

## Demo credentials
All demo accounts use password `demo123`:
- owner@setustock.demo
- manager@setustock.demo
- sales@setustock.demo
- warehouse@setustock.demo
- accountant@setustock.demo
