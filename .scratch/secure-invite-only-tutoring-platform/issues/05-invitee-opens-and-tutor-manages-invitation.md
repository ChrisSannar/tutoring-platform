# 05 — Invitee Opens and Tutor Manages an Invitation

**What to build:** An Invitee can safely open their personalized setup page while the Tutor can correct, revoke, or regenerate the underlying Invitation.

**Blocked by:** 04 — Tutor Creates a Personalized Invitation.

**Status:** ready-for-agent

- [ ] The setup page exposes only the Shared Personal Message and allowlisted Invitee data.
- [ ] The Tutor can correct the bound email before claim, revoke, and regenerate.
- [ ] Regeneration permanently invalidates the prior token and reveals the replacement once.
- [ ] Invalid, expired, revoked, claimed, and superseded tokens fail with safe indistinguishable responses.
- [ ] Browser and black-box tests cover the lifecycle through public behavior.
