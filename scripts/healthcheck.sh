#!/usr/bin/env bash
set -euo pipefail
URL="${1:-http://127.0.0.1:8000/api/health/}"
curl --fail --silent --show-error "$URL"
