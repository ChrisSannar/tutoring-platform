# 04 — Tutor Creates a Personalized Invitation

**What to build:** The authenticated Tutor can create and activate a secure personalized Invitation for a known Invitee without leaking Private Tutor Notes.

**Blocked by:** 03 — Invite-Only Tutor Authentication.

**Status:** resolved

- [x] Invitation creation binds a normalized email and separates private and shared content.
- [x] Activation returns the raw seven-day token once while storing only its hash.
- [x] Anonymous and Student callers cannot create or inspect Tutor Invitation records.
- [x] Public response models cannot serialize Private Tutor Notes.
- [x] The Tutor UI and black-box negative paths are tested through confirmed seams.

## Answer

Implemented the authenticated Tutor workflow to create a draft Invitation with a
normalized Invitee email, distinct Shared Personal Message and Private Tutor Note,
then activate it into a seven-day opaque link. The raw link is returned only from the
successful activation response; persistence stores its hash, and later Tutor inspection
cannot retrieve it. Tutor mutations require the authenticated Tutor's session-bound
CSRF token and same-origin request, while anonymous and Student callers cannot create
or inspect Tutor Invitation records. Explicit response models keep Private Tutor Notes
out of the activation boundary. Black-box HTTP tests cover the trust boundary and
Playwright covers the visible Tutor creation and activation flow. `bun run test` passes
with 29 backend tests and 5 Playwright tests.
