# 03 — One-step Student account claim

**What to build:** Turn one active Invitation Link into a minimal, scanner-safe account setup that atomically creates the Student relationship and signs the Student into their dashboard.

**Blocked by:** 02 — Retrievable Invitation Link management.

**Status:** ready-for-agent

- [ ] Opening an active Invitation Link only displays setup information and records first successful opening; it does not consume the link or create an account.
- [ ] The setup page shows the normalized bound email as read-only and accepts only a required display name.
- [ ] **Create Account** atomically claims the Invitation, creates one Student account, creates a new Student Session, and grants the First Session Promotion through the Credit Ledger.
- [ ] Successful claim routes directly to the Student Dashboard without a second verification or Login Link.
- [ ] Concurrent claims have exactly one winner, and an email already owned by an account cannot create a duplicate Student.
- [ ] Claim erases retrievable Invitation token material and makes the Invitation unusable.
- [ ] A claimed Invitee appears in the Tutor's Student list and any linked Inquiry leaves the active Inquiry queue.
- [ ] Existing secure-cookie, session-expiration, rotation, logout, and role-authorization contracts remain intact.
- [ ] Black-box concurrency and authorization tests prove atomic account, session, promotion, and Invitation outcomes.

