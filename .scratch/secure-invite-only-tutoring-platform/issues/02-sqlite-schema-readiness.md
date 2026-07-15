# 02 — SQLite Schema Readiness

**What to build:** Operators can distinguish a live API from one that can safely use its explicitly migrated SQLite schema, while local and browser tests remain isolated from persistent data.

**Blocked by:** 01 — Public Application Shell and Liveness.

**Status:** resolved

- [x] Alembic is the sole schema authority and migrations run outside the API process.
- [x] `GET /api/ready` returns the exact ready response only for reachable schema at head.
- [x] Database and schema failures return their exact sanitized 503 responses.
- [x] Development, E2E, and non-development database configuration obey the accepted boundaries.
- [x] Black-box HTTP and Playwright coverage prove isolated migration and cleanup behavior.

## Comments

- Implemented through red-green slices at the confirmed black-box HTTP and Playwright seams.
- The root E2E harness creates, migrates, and removes one temporary SQLite directory while preserving the Playwright exit status.
- Verified all backend and browser behavior with `bun run test` from the repository root.
