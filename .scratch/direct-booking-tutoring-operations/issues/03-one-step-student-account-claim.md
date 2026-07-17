# 03 — One-step Student account claim

**What to build:** Turn one active Invitation Link into a minimal, scanner-safe account setup that atomically creates the Student relationship and signs the Student into their dashboard.

**Blocked by:** 02 — Retrievable Invitation Link management.

**Status:** resolved

- [x] Opening an active Invitation Link only displays setup information and records first successful opening; it does not consume the link or create an account.
- [x] The setup page shows the normalized bound email as read-only and accepts only a required display name.
- [x] **Create Account** atomically claims the Invitation, creates one Student account, creates a new Student Session, and grants the First Session Promotion through the Credit Ledger.
- [x] Successful claim routes directly to the Student Dashboard without a second verification or Login Link.
- [x] Concurrent claims have exactly one winner, and an email already owned by an account cannot create a duplicate Student.
- [x] Claim erases retrievable Invitation token material and makes the Invitation unusable.
- [x] A claimed Invitee appears in the Tutor's Student list and any linked Inquiry leaves the active Inquiry queue.
- [x] Existing secure-cookie, session-expiration, rotation, logout, and role-authorization contracts remain intact.
- [x] Black-box concurrency and authorization tests prove atomic account, session, promotion, and Invitation outcomes.

## Answer

Replaced the two-link browser ceremony with one scanner-safe setup page and an atomic
claim using the original Invitation Link. The claim creates the Student account and
server-side session, appends a distinct First Session Promotion event to the immutable
Credit Ledger, erases Invitation access material, and archives any linked Inquiry in
one transaction. The Tutor Student list reflects the completed role transition.

Concurrent claims produce one winner, duplicate normalized account email is denied,
and display-name validation plus existing session, rotation, logout, and authorization
coverage remain green. Verification: 81 backend tests, 12 Playwright tests, and the
frontend production build pass. See the Ticket 03 entry in `../map.md`.
