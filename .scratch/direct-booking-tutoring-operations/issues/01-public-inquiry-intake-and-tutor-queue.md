# 01 — Public Inquiry intake and Tutor queue

**What to build:** Give a Prospect one clear way to request tutoring from the landing page, and give the Tutor a private queue for reviewing and disposing of those Inquiries without granting application access.

**Blocked by:** None — can start immediately.

**Status:** resolved

- [x] The public landing page presents one primary **Request tutoring** action that opens an Inquiry modal without navigating away.
- [x] A Prospect can submit a normalized valid email and a required plain-text contextual message no longer than 2,000 characters.
- [x] Successful submission creates a separate Inquiry for every request and shows an on-page confirmation without creating an account or revealing private state.
- [x] Anonymous submissions are limited to five per hashed IP per hour, and validation, rate-limit, and unexpected errors use safe public responses.
- [x] Anonymous and Student callers cannot list or mutate Inquiries.
- [x] The Tutor Dashboard lists active New and Invited Inquiries with safely rendered email, message, and state.
- [x] The Tutor can archive an Inquiry and can permanently delete one only after explicit confirmation.
- [x] Black-box HTTP tests cover validation, normalization, repetition, rate limiting, authorization, archive, delete, and sensitive-data response boundaries.

## Answer

Implemented the public Inquiry modal, generic confirmation, normalized and bounded
submission API, per-hashed-IP hourly limit, Tutor-only allowlisted queue, archive, and
confirmed permanent deletion. Added Alembic-managed persistence, black-box HTTP
coverage, and Playwright coverage for the Prospect and Tutor flows. The isolated E2E
harness now uses dedicated ports so it owns its processes without colliding with local
development servers.

Verified with 70 passing backend tests, 12 passing Playwright tests, and a successful
frontend production build. See the Ticket 01 entry in `../map.md`.
