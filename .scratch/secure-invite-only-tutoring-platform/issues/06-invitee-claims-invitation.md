# 06 — Invitee Claims the Invitation

**What to build:** The intended Invitee can verify the bound email, edit their display name, atomically claim the Invitation, and continue through a secure Student Session.

**Blocked by:** 05 — Invitee Opens and Tutor Manages an Invitation.

**Status:** resolved

- [x] Only the verified bound email can complete Invitation Claim.
- [x] The display name is editable without making the email mutable.
- [x] Claim is atomic and cannot succeed twice or associate multiple accounts.
- [x] Successful claim creates and rotates an opaque server-side Student Session.
- [x] Confirmation, failure, concurrency, and browser behavior are tested at confirmed seams.

## Answer

Implemented bound-email verification and explicit confirmation before Invitation Claim.
The atomic claim updates the Invitation, creates exactly one Student account, consumes
the one-use verification token, rotates any prior browser authentication, and creates an
opaque server-side Student Session in one transaction. The browser keeps the bound email
immutable while allowing the Invitee to edit their display name, then continues into a
persistent Student workspace.

Verified with `bun run test`: 42 backend tests and 9 Playwright tests passed, including
a live two-worker black-box HTTP concurrency test with exactly one successful claimant.
