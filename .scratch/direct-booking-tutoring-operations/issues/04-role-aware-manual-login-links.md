# 04 — Role-aware manual Login Links

**What to build:** Give returning account holders one role-neutral login request flow while retaining the personalized, manual-email boundary for delivering short-lived Login Links.

**Blocked by:** None — can start immediately.

**Status:** ready-for-agent

- [ ] The public **Log In** action opens one role-neutral Login Request form for Tutor and Student accounts.
- [ ] Eligible and ineligible submissions receive the same public response and remain protected by email/IP abuse limits.
- [ ] An eligible Student request appears only in the Tutor's active Login Request queue and does not create a Login Link until Tutor action.
- [ ] The Tutor can generate and copy a single-use Login Link whose 15-minute lifetime starts at generation time.
- [ ] Used, expired, and Tutor-dismissed Login Requests leave the active queue.
- [ ] Login Link GET is observational, while explicit POST confirmation consumes the link, rotates prior browser authentication, and creates the new role session.
- [ ] Successful confirmation routes the account holder to the dashboard for their actual role.
- [ ] A repository command generates a short-lived Tutor Login Link without dashboard access and emits the plaintext value only as sensitive one-time output.
- [ ] The landing utility shows **Dashboard** instead of **Log In** when an active session exists.
- [ ] Black-box tests cover enumeration resistance, delayed generation, expiry, replay, rotation, cross-role denial, routing, and the Tutor command.

