# SetuStock production deployment

## Required production controls

- Set a unique `DJANGO_SECRET_KEY`, `DB_PASSWORD`, `DJANGO_ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS` and `CSRF_TRUSTED_ORIGINS`.
- Keep `DJANGO_DEBUG=false`, `SECURE_SSL_REDIRECT=true`, HTTPS termination enabled, and database/media volumes persistent.
- Point `VITE_API_URL` at the public HTTPS API URL before building the frontend.
- Configure an external error tracker through `SENTRY_DSN` and use `RELEASE_VERSION` for release correlation.

## Release checks

```bash
docker compose up -d --build
docker compose ps
curl -fsS https://api.example.com/api/ready/
```

The API readiness endpoint checks the database. The frontend and backend containers also expose Docker health checks for orchestration.

## Database backup and restore

Run `scripts/backup_postgres.sh` from an environment with PostgreSQL client tools and database credentials. The script writes a checksum beside every dump and supports `BACKUP_RETENTION_DAYS`.

```bash
BACKUP_DIR=/var/backups/setustock BACKUP_RETENTION_DAYS=30 scripts/backup_postgres.sh
scripts/restore_postgres.sh /var/backups/setustock/setustock-YYYYMMDD-HHMMSS.dump
```

Test a restore into a separate database at least monthly. Do not overwrite the primary database during a restore drill.

## Monitoring and alerts

- Poll `/api/health/` for process health and `/api/ready/` for database readiness.
- Alert on a non-2xx response, container health failure, backup age over 24 hours, failed background jobs, failed webhooks, and rising offline-sync conflicts.
- Send application exceptions to the configured error tracker and retain structured audit logs for operational investigations.
