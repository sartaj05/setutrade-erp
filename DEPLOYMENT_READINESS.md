# Deployment readiness

Use this gate before a client demo becomes a live tenant deployment.

## Required controls

- Set a long, unique `DJANGO_SECRET_KEY`; keep it in a secret manager.
- Set `DJANGO_DEBUG=false`, explicit `DJANGO_ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, and `CSRF_TRUSTED_ORIGINS`.
- Use PostgreSQL, run migrations, collect static assets, and run `python manage.py check --deploy`.
- Set `VITE_APP_MODE=production` and `VITE_DEMO_FALLBACK=false` in the frontend build.
- Terminate TLS at the reverse proxy and set `SECURE_SSL_REDIRECT=true` behind HTTPS.
- Configure SMTP for password reset and a real object-storage strategy for uploaded files.
- Verify `/api/health/` for liveness and `/api/ready/` for database/migration readiness from outside the private network.
- Schedule database/media backups and test a restore before onboarding the client.
- Monitor 5xx responses, failed jobs, webhook retries, login lockouts, disk usage, and backup age.

## Compose smoke test

```bash
docker compose up --build -d
docker compose ps
curl http://localhost:8000/api/health/
```

The backend readiness check blocks the frontend until Django and its database/migrations are ready. The local Compose profile intentionally disables HTTPS redirect for local testing; production must use the environment values above behind an HTTPS proxy.
