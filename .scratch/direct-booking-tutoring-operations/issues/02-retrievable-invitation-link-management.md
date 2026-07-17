# 02 — Retrievable Invitation Link management

**What to build:** Let the Tutor create and manually deliver a single active Invitation Link, retrieve it while it remains usable, and safely replace or terminate it without exposing plaintext access material at rest.

**Blocked by:** 01 — Public Inquiry intake and Tutor queue.

**Status:** ready-for-agent

- [ ] A short ADR records the decision to store a hash for lookup and a separately encrypted, Tutor-retrievable Invitation Link until a terminal state.
- [ ] From an active Inquiry, the Tutor can create one seven-day Invitation Link in a single action and the Inquiry becomes Invited.
- [ ] The Tutor can also create an Invitation from a normalized email without manufacturing an Inquiry.
- [ ] An authenticated Tutor can copy the current Invitation Link until it is claimed, revoked, expired, or regenerated; no other role can retrieve it.
- [ ] The Tutor can regenerate a link, atomically invalidating and erasing the previous hash/ciphertext before receiving the replacement.
- [ ] The Tutor can revoke an Invitation, and expired Invitations become unusable without requiring a background scheduler.
- [ ] Token ciphertext is erased after claim, revocation, expiration, or regeneration and is excluded from ordinary responses and logs.
- [ ] Non-development configuration fails closed when the Invitation encryption key is missing or invalid.
- [ ] Black-box HTTP tests cover Inquiry-linked and manual creation, encrypted redisplay, authorization, expiration, regeneration, revocation, and terminal erasure.

