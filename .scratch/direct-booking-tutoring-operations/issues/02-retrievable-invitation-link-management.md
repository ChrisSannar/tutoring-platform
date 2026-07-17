# 02 — Retrievable Invitation Link management

**What to build:** Let the Tutor create and manually deliver a single active Invitation Link, retrieve it while it remains usable, and safely replace or terminate it without exposing plaintext access material at rest.

**Blocked by:** 01 — Public Inquiry intake and Tutor queue.

**Status:** resolved

- [x] A short ADR records the decision to store a hash for lookup and a separately encrypted, Tutor-retrievable Invitation Link until a terminal state.
- [x] From an active Inquiry, the Tutor can create one seven-day Invitation Link in a single action and the Inquiry becomes Invited.
- [x] The Tutor can also create an Invitation from a normalized email without manufacturing an Inquiry.
- [x] An authenticated Tutor can copy the current Invitation Link until it is claimed, revoked, expired, or regenerated; no other role can retrieve it.
- [x] The Tutor can regenerate a link, atomically invalidating and erasing the previous hash/ciphertext before receiving the replacement.
- [x] The Tutor can revoke an Invitation, and expired Invitations become unusable without requiring a background scheduler.
- [x] Token ciphertext is erased after claim, revocation, expiration, or regeneration and is excluded from ordinary responses and logs.
- [x] Non-development configuration fails closed when the Invitation encryption key is missing or invalid.
- [x] Black-box HTTP tests cover Inquiry-linked and manual creation, encrypted redisplay, authorization, expiration, regeneration, revocation, and terminal erasure.

## Answer

Recorded ADR 0004 and implemented hash-based lookup with separately authenticated
Fernet ciphertext for Tutor redisplay. Manual email creation and Inquiry-linked creation
now issue a seven-day `created` Invitation in one action; successful setup reads record
the observational `opened` state. The Tutor can retrieve, regenerate, and revoke links,
while claim, revocation, lazy expiration, and regeneration remove or replace access
material atomically.

The Tutor UI now exposes one-step manual creation plus Inquiry-scoped creation and link
management. Non-development configuration requires a valid operator key. Verification:
77 backend tests, 12 Playwright tests, and the frontend production build pass. See the
Ticket 02 entry in `../map.md`.
