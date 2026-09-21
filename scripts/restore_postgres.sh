#!/usr/bin/env bash
set -euo pipefail
FILE="${1:?Usage: restore_postgres.sh <backup.dump>}"
: "${DB_NAME:?DB_NAME required}" "${DB_USER:?DB_USER required}" "${DB_HOST:?DB_HOST required}"
pg_restore --clean --if-exists --no-owner --host="$DB_HOST" --port="${DB_PORT:-5432}" --username="$DB_USER" --dbname="$DB_NAME" "$FILE"
