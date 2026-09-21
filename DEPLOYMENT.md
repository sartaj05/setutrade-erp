# Deployment guide

## A. Frontend-only sales demo

Use Vercel, Netlify, Cloudflare Pages, or any static host.

- Root: `frontend`
- Build: `npm run build`
- Output: `dist`

Environment:

```env
VITE_APP_MODE=demo
VITE_DEMO_FALLBACK=true
VITE_API_URL=https://unused.example/api
```

This mode is for demonstration data only.

## B. Production deployment

Recommended topology:

```text
React static host / CDN
        |
      HTTPS
        |
Django + Gunicorn
        |
    PostgreSQL
        |
backup/object storage
```

Backend minimum environment:

```env
DJANGO_SECRET_KEY=<long-random-secret>
DJANGO_DEBUG=false
DJANGO_ALLOWED_HOSTS=api.example.com
CORS_ALLOWED_ORIGINS=https://app.example.com
CSRF_TRUSTED_ORIGINS=https://app.example.com
SECURE_SSL_REDIRECT=true
DB_ENGINE=django.db.backends.postgresql
DB_NAME=setustock
DB_USER=setustock
DB_PASSWORD=<secret>
DB_HOST=<postgres-host>
DB_PORT=5432
FRONTEND_URL=https://app.example.com
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=<smtp-host>
EMAIL_PORT=587
EMAIL_HOST_USER=<smtp-user>
EMAIL_HOST_PASSWORD=<smtp-secret>
DEFAULT_FROM_EMAIL=noreply@example.com
SETUSTOCK_DEMO_MODE=false
```

Frontend:

```env
VITE_APP_MODE=production
VITE_API_URL=https://api.example.com/api
VITE_DEMO_FALLBACK=false
```

Deploy backend:

```bash
pip install -r requirements.txt
python manage.py migrate --noinput
python manage.py collectstatic --noinput
python manage.py check --deploy
gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
```

Do **not** run `seed_demo` against the live client database.

## C. Docker Compose

```bash
export DJANGO_SECRET_KEY='replace-me'
export DB_PASSWORD='replace-me'
docker compose up --build
```

The Compose stack provides PostgreSQL, Django/Gunicorn and an Nginx-served React production build.

## Backups

Scripts are in `scripts/`:

```bash
./scripts/backup_postgres.sh
./scripts/restore_postgres.sh backups/<file>.dump
./scripts/healthcheck.sh http://localhost:8000/api/health/
```

Set `DATABASE_URL`-style variables as described inside the scripts or use the Docker defaults. Test restores regularly.

## Uploaded files

The Docker stack persists `backend/media` in a named volume. For scalable/cloud production, move Django's default file storage to S3-compatible object storage and use private/signed URLs where appropriate.

## Optional integrations

```env
WHATSAPP_ACCESS_TOKEN=
WHATSAPP_PHONE_NUMBER_ID=
GST_PROVIDER_API_KEY=
```

The WhatsApp adapter can send outbound text when valid Meta credentials are configured. GST provider credentials are represented as readiness/configuration only; connect and test the authorised provider API before treating e-invoice/e-way-bill generation as live.

## Monitoring

- Poll `/api/health/` from an external uptime service.
- Centralise Gunicorn/application logs.
- Add an error/APM product suitable for the client's infrastructure.
- Alert on failed backups, database disk growth and elevated 5xx rates.
