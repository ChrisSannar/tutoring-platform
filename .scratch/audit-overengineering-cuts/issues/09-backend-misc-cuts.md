# 09 — Backend misc cuts: refund DI and migration squash

**What to build:** Two cuts:
1. Remove `ApplicationContext.refund_payment` (Callable field + deferred import +
   lambda, one caller in `routes/refunds.py`) — call
   `app.refunds.provider.refund_payment` directly with settings there. KEEP
   `context.now` (test clock depends on it).
2. Squash `backend/migrations/versions/` (18 files / 761 lines, incl. a
   create-table migration dropped 2 days later by another, plus its 50-line test
   `test_session_request_retirement.py`) into ONE initial migration producing the
   current schema. Tests build fresh DBs via alembic, so the suite verifies the
   squash. Delete `tests/test_session_request_retirement.py` with the dead pair.
   Note in the commit message that dev DBs (`backend/var`) must be recreated.

**Blocked by:** 03

**Status:** ready-for-agent

- [ ] refund_payment called directly; DI plumbing deleted
- [ ] One initial migration; alembic upgrade head on a fresh DB reproduces the schema
- [ ] `test_session_request_retirement.py` deleted
- [ ] `bun run test:backend` passes
- [ ] Two commits (one per cut)
