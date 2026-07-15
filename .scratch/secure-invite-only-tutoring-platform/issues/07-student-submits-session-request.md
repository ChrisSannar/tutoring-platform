# 07 — Student Submits a Session Request

**What to build:** A Student can submit one pending Session Request and the Tutor can view it, completing the required end-to-end product journey.

**Blocked by:** 06 — Invitee Claims the Invitation.

**Status:** resolved

- [x] Requests require service, preferred start, IANA timezone, and a bounded optional message.
- [x] Preferred time is stored consistently in UTC and new requests remain pending.
- [x] Per-Student idempotency prevents duplicate requests while preserving safe retries.
- [x] Students cannot access another Student's requests and the Tutor can view all business requests.
- [x] Playwright covers landing through Tutor visibility; black-box tests cover validation, ownership, CSRF, and idempotency.

## Answer

Implemented the pending Session Request flow through the black-box HTTP and Playwright
seams. Student submissions validate required service, preferred start, IANA timezone,
and the 1,000-character optional message, normalize preferred starts to UTC, require
same-origin CSRF protection, and use per-Student idempotency keys for safe retries.
Student reads are ownership-constrained while the Tutor can view all business requests.
The browser journey now runs from the public landing page through Invitation Claim,
Student submission, and Tutor visibility without introducing Booking behavior.

Verification: `bun run test` passed 58 backend tests and 9 Playwright tests.
