# 05 — Invitee Opens and Tutor Manages an Invitation

**What to build:** An Invitee can safely open their personalized setup page while the Tutor can correct, revoke, or regenerate the underlying Invitation.

**Blocked by:** 04 — Tutor Creates a Personalized Invitation.

**Status:** resolved

- [x] The setup page exposes only the Shared Personal Message and allowlisted Invitee data.
- [x] The Tutor can correct the bound email before claim, revoke, and regenerate.
- [x] Regeneration permanently invalidates the prior token and reveals the replacement once.
- [x] Invalid, expired, revoked, claimed, and superseded tokens fail with safe indistinguishable responses.
- [x] Browser and black-box tests cover the lifecycle through public behavior.

## Answer

Implemented the public Invitee setup page and authenticated Tutor controls for email
correction, revocation, and token regeneration. Invitee responses use an explicit
allowlist and never include the Private Tutor Note. Regeneration replaces the stored
token hash, expired links transition the Invitation to `expired`, and every unusable
token state returns the same sanitized not-found response.

Verified with `bun run test`: 35 backend tests and 8 Playwright tests passed.
