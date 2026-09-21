# SetuStock NCR

A demo-ready B2B wholesale/distribution management SaaS for Delhi NCR businesses.

## Stack
- Frontend: React 19 + Vite 8 + plain CSS
- Backend: Django 6 core APIs using `JsonResponse` and Django signing (no DRF)
- Database: SQLite for demo, PostgreSQL-ready via environment settings

## Core modules
- Role based access: OWNER, MANAGER, SALES, WAREHOUSE, ACCOUNTANT
- Dashboard
- Products & inventory
- Customers & credit/udhaari
- B2B orders
- GST invoice-ready data model
- Quotations placeholder workflow
- Payments placeholder workflow
- WhatsApp action links
- Public landing page + login
- Offline/demo fallback data when backend is not connected

## Demo accounts
Password for every demo account: `demo123`

- owner@setustock.demo
- manager@setustock.demo
- sales@setustock.demo
- warehouse@setustock.demo
- accountant@setustock.demo

## Run frontend
```bash
cd frontend
npm install
npm run dev
```

## Run backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

## Environment
Copy `frontend/.env.example` to `frontend/.env` and `backend/.env.example` to `backend/.env`.

The frontend first tries the Django API. If the API is unavailable, it automatically switches to demo mode unless `VITE_DEMO_FALLBACK=false`.

## Feature-wise git history
This repository is intentionally committed feature-by-feature. Run:

```bash
git log --oneline --reverse
```

## Deployment
- Frontend: Vercel / Netlify / Cloudflare Pages
- Backend: Render / Railway / Fly.io / VPS
- Production database: PostgreSQL

See `DEPLOYMENT.md` for deployment notes.
