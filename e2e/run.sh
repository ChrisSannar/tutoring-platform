#!/usr/bin/env bash
set -euo pipefail

state_directory="$(mktemp -d /tmp/tutoring-platform-e2e.XXXXXX)"

cleanup() {
  rm -rf "${state_directory}"
}

trap cleanup EXIT INT TERM

export TUTORING_ENVIRONMENT=test
export TUTORING_DATABASE_URL="sqlite:///${state_directory}/test.sqlite3"

UV_CACHE_DIR=/tmp/tutoring-platform-uv-cache \
  uv run --project backend alembic -c backend/alembic.ini upgrade head
UV_CACHE_DIR=/tmp/tutoring-platform-uv-cache \
  uv run --project backend python -m app.bootstrap_tutor tutor@example.com

status=0
PLAYWRIGHT_BROWSERS_PATH=/tmp/tutoring-platform-playwright \
  playwright test --config e2e/playwright.config.ts || status=$?

cleanup
if [[ -e "${state_directory}" ]]; then
  echo "E2E state cleanup failed" >&2
  exit 1
fi
trap - EXIT
exit "${status}"
