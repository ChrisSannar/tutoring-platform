# Current Handoff — 2026-07-15

## Completed

- Finished the product grilling for the secure, invite-only, single-Tutor platform.
- Recorded the accepted product/security decisions in `docs/PRODUCT-GRILLING.md` and
  `docs/PRODUCT-DECISION-SHEET.md`.
- Established canonical domain language in `CONTEXT.md` and three architecture ADRs.
- Configured the engineering skills for a local Markdown tracker through `AGENTS.md`
  and `docs/agents/`.
- Published the `ready-for-agent` spec at
  `.scratch/secure-invite-only-tutoring-platform/spec.md`.
- Published eight approved, linear tracer-bullet tickets beneath
  `.scratch/secure-invite-only-tutoring-platform/issues/`.
- Completed ticket 01 with a public React landing page, sanitized FastAPI liveness,
  browser security headers, locked dependencies, and root-owned Playwright orchestration.
- Confirmed TDD seams:
  1. Playwright for the full user journey.
  2. Black-box HTTP tests for API and security behavior.

## Approved ticket order

1. Public Application Shell and Liveness — resolved
2. SQLite Schema Readiness
3. Invite-Only Tutor Authentication
4. Tutor Creates a Personalized Invitation
5. Invitee Opens and Tutor Manages an Invitation
6. Invitee Claims the Invitation
7. Student Submits a Session Request
8. Tutor Deletes Collected Pilot Data

Each ticket is blocked by the preceding ticket. Implement with red-green TDD and commit
each completed ticket separately.

## Current repository state

- The planning/domain baseline is committed.
- Ticket 01 application code is implemented, verified, and committed separately from
  the planning baseline.
- Root `bun run setup` performs frozen Bun installation and locked Python synchronization.
- Root `bun run test` runs black-box HTTP and Playwright behavior checks.
- Git index writes require escalation because `.git` is read-only in the normal sandbox.

## Restart sequence

1. Read `AGENTS.md`, `CONTEXT.md`, ADR 0002, the spec, and ticket 02.
2. Check `git status` and confirm the ticket 01 implementation commit exists.
3. Implement ticket 02 test-first at the confirmed black-box HTTP seam:
   - first produce a failing external-behavior test;
   - add only enough implementation to pass;
   - run the relevant checks;
   - commit ticket 02 by itself.
4. Continue tickets 03 through 08 in dependency order, one verified commit per ticket.

## Key Day 1 contracts

- React/TypeScript/Bun/Vite frontend and FastAPI/SQLite backend.
- Synchronous SQLAlchemy 2.x with Alembic; the API never applies migrations itself.
- Public `GET /api/health` returns only `{"status":"ok"}`.
- Public `GET /api/ready` checks database access and Alembic head, returning sanitized
  `database` or `schema` failure reasons.
- `bun run test:e2e` owns a temporary migrated database, both application processes,
  Playwright execution, teardown, and cleanup without pre-running services.
- Security is a completion gate for every slice.
