# 04 — Role-aware manual Login Links

**What to build:** Give returning account holders one role-neutral login request flow while retaining the personalized, manual-email boundary for delivering short-lived Login Links.

**Blocked by:** None — can start immediately.

**Status:** resolved

- [x] The public **Log In** action opens one role-neutral Login Request form for Tutor and Student accounts.
- [x] Eligible and ineligible submissions receive the same public response and remain protected by email/IP abuse limits.
- [x] An eligible Student request appears only in the Tutor's active Login Request queue and does not create a Login Link until Tutor action.
- [x] The Tutor can generate and copy a single-use Login Link whose 15-minute lifetime starts at generation time.
- [x] Used, expired, and Tutor-dismissed Login Requests leave the active queue.
- [x] Login Link GET is observational, while explicit POST confirmation consumes the link, rotates prior browser authentication, and creates the new role session.
- [x] Successful confirmation routes the account holder to the dashboard for their actual role.
- [x] A repository command generates a short-lived Tutor Login Link without dashboard access and emits the plaintext value only as sensitive one-time output.
- [x] The landing utility shows **Dashboard** instead of **Log In** when an active session exists.
- [x] Black-box tests cover enumeration resistance, delayed generation, expiry, replay, rotation, cross-role denial, routing, and the Tutor command.

## Answer

The landing page now provides one role-neutral Login Request form and an authenticated
Dashboard utility. Student requests enter a Tutor-only queue without creating a token;
Tutor generation starts the 15-minute lifetime and exposes the plaintext only in that
response for copying. Consumption, expiry, and dismissal remove requests from active
work, with dismissal also invalidating an already-generated token. Confirmation remains
observational on GET, explicit on POST, rotates prior authentication, and routes by the
account's stored role. `bun run tutor:login-link` provides the one-time Tutor recovery
path. Verification: 92 backend tests and 13 Playwright journeys pass.
