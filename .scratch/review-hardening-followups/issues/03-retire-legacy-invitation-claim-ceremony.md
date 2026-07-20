# 03 — Retire the legacy Invitation Claim ceremony

**What to build:** Make the scanner-safe, one-step Invitation Claim the only onboarding journey so an Invitee cannot enter the superseded second-link or draft-activation flows.

**Blocked by:** None — can start immediately.

**Status:** resolved

- [x] Public onboarding exposes only the read-only bound email, required display name, and explicit Create Account action from the original Invitation Link.
- [x] The legacy endpoint that asks an Invitee to re-enter an email and issues a second claim link is no longer reachable.
- [x] The legacy second-link inspection and consumption endpoints, implementation paths, response models, and browser routes are removed when no longer used.
- [x] Tutor-facing Invitation creation no longer exposes the superseded draft-to-activation ceremony.
- [x] Existing one-step claim behavior still atomically creates the Student account and Student Session, grants the First Session Promotion, erases token material, and archives any linked Inquiry.
- [x] Black-box and browser tests prove the one-step path and prove that the retired paths are unavailable.

## Answer

The original Invitation Link is now the only Invitee onboarding path. The public API
retains observational Invitation opening and atomic one-step account creation, while the
second-link request, inspection, and consumption endpoints and the Tutor draft activation
endpoint are unavailable. Their unused route, implementation, response-model, and browser
code was removed. Tutor Invitation creation now accepts only the one-action email request.

Existing black-box coverage continues to prove Student account and Student Session
creation, First Session Promotion funding, token invalidation, linked Inquiry archival,
session rotation, and exactly-one-winner concurrency. Browser coverage proves the original
Invitation displays only the bound email, required display name, and Create Account action,
and that the retired confirmation route no longer renders its former journey.

## Comments

- Red: the retired API test observed `202`, `400`, and `401` responses instead of `404`.
- Red: the superseded Tutor draft payload was accepted with `201` instead of rejected with
  `422`.
- Red: the retired browser route did not render the public landing page.
- Green: targeted API verification passed 32 tests with one live concurrency test excluded;
  the separate real two-worker concurrency test passed; the targeted browser retirement
  test passed.
- Green: the authoritative command passed 94 backend tests and 13 Playwright tests:
  `BUN_INSTALL=/tmp/bun BUN_TMPDIR=/tmp UV_CACHE_DIR=/tmp/tutoring-platform-uv-cache PLAYWRIGHT_BROWSERS_PATH=/tmp/tutoring-platform-playwright bun run test`.
