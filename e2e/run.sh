#!/usr/bin/env bash
set -euo pipefail

state_directory="$(mktemp -d /tmp/tutoring-platform-e2e.XXXXXX)"
port_offset=$((RANDOM % 10000))
export E2E_FRONTEND_PORT=$((30000 + port_offset))
export E2E_BACKEND_PORT=$((40000 + port_offset))

cleanup() {
  rm -rf "${state_directory}"
}

trap cleanup EXIT INT TERM

export TUTORING_ENVIRONMENT=test
export TUTORING_DATABASE_URL="sqlite:///${state_directory}/test.sqlite3"
export TUTORING_APPLICATION_ORIGIN="http://127.0.0.1:${E2E_FRONTEND_PORT}"
export TUTORING_INVITATION_ENCRYPTION_KEY="a2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2s="
export TUTORING_MAGIC_LINK_EMAIL_HOURLY_LIMIT=50
export TUTORING_MAGIC_LINK_IP_HOURLY_LIMIT=100
export VITE_API_PROXY_TARGET="http://127.0.0.1:${E2E_BACKEND_PORT}"

UV_CACHE_DIR=/tmp/tutoring-platform-uv-cache \
  uv run --project backend alembic -c backend/alembic.ini upgrade head
UV_CACHE_DIR=/tmp/tutoring-platform-uv-cache \
  uv run --project backend python -m app.bootstrap_tutor tutor@example.com

status=0
PLAYWRIGHT_BROWSERS_PATH=/tmp/tutoring-platform-playwright \
  playwright test --config e2e/playwright.config.ts "$@" || status=$?

cleanup
if [[ -e "${state_directory}" ]]; then
  echo "E2E state cleanup failed" >&2
  exit 1
fi
trap - EXIT
exit "${status}"
