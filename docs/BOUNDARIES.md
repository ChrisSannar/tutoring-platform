# Tutoring Platform — Frozen Three-Day Boundaries

Every daily boundary is subject to the security completion gate in
[`PRODUCT-GRILLING.md`](PRODUCT-GRILLING.md); functionality without its required
security boundaries and negative-path tests is incomplete.

## Required slice

`landing page → personalized invitation → account claim → session request`

## Day 1 — Foundation (July 15)

- Complete accountability preflight.
- Establish React/TypeScript/Bun/Vite and Python/FastAPI/SQLite layers.
- Build a tested landing page, liveness-only `GET /api/health` route, and
  database/schema-aware `GET /api/ready` route with sanitized failure responses.
- Establish `bun run test:e2e` as the repository-local Playwright command that owns an
  isolated migrated SQLite database plus both application processes and their cleanup.

## Day 2 — Personalized invitation (July 16)

- Tutor creates an invitation with an opaque token.
- Private tutor notes remain separate from the invitee-visible message.
- Invitee opens the personalized setup page.
- Persist lifecycle state and test authorization, invalid-token, and revocation behavior.

## Day 3 — Claim and request (July 17)

- Invitee claims through a development-outbox magic link.
- Claim creates a server-side session and prevents a second account claim.
- Student submits a session request and tutor can see it.
- Finish the critical-path E2E, regressions, and mastery evidence.

## Optional backlog only

Calendar sync, payment, real email, deployment, reminders, lesson notes, files,
rescheduling, cancellation, social login, and visual browser grading.
