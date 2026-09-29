#!/usr/bin/env bash
set -euo pipefail
: "${DB_NAME:?DB_NAME required}" "${DB_USER:?DB_USER required}" "${DB_HOST:?DB_HOST required}"
OUT_DIR="${BACKUP_DIR:-./backups}"
mkdir -p "$OUT_DIR"
STAMP="$(date +%Y%m%d-%H%M%S)"
FILE="$OUT_DIR/setustock-$STAMP.dump"
pg_dump --format=custom --no-owner --host="$DB_HOST" --port="${DB_PORT:-5432}" --username="$DB_USER" "$DB_NAME" > "$FILE"
sha256sum "$FILE" > "$FILE.sha256"
if [ -n "${BACKUP_RETENTION_DAYS:-}" ]; then
  find "$OUT_DIR" -type f -name 'setustock-*.dump' -mtime "+${BACKUP_RETENTION_DAYS}" -delete
  find "$OUT_DIR" -type f -name 'setustock-*.dump.sha256' -mtime "+${BACKUP_RETENTION_DAYS}" -delete
fi
echo "$FILE"
