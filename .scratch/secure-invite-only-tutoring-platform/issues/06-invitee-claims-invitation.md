# 06 — Invitee Claims the Invitation

**What to build:** The intended Invitee can verify the bound email, edit their display name, atomically claim the Invitation, and continue through a secure Student Session.

**Blocked by:** 05 — Invitee Opens and Tutor Manages an Invitation.

**Status:** ready-for-agent

- [ ] Only the verified bound email can complete Invitation Claim.
- [ ] The display name is editable without making the email mutable.
- [ ] Claim is atomic and cannot succeed twice or associate multiple accounts.
- [ ] Successful claim creates and rotates an opaque server-side Student Session.
- [ ] Confirmation, failure, concurrency, and browser behavior are tested at confirmed seams.
