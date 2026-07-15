# 02 — SQLite Schema Readiness

**What to build:** Operators can distinguish a live API from one that can safely use its explicitly migrated SQLite schema, while local and browser tests remain isolated from persistent data.

**Blocked by:** 01 — Public Application Shell and Liveness.

**Status:** ready-for-agent

- [ ] Alembic is the sole schema authority and migrations run outside the API process.
- [ ] `GET /api/ready` returns the exact ready response only for reachable schema at head.
- [ ] Database and schema failures return their exact sanitized 503 responses.
- [ ] Development, E2E, and non-development database configuration obey the accepted boundaries.
- [ ] Black-box HTTP and Playwright coverage prove isolated migration and cleanup behavior.
