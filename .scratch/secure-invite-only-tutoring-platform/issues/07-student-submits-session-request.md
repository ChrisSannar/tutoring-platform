# 07 — Student Submits a Session Request

**What to build:** A Student can submit one pending Session Request and the Tutor can view it, completing the required end-to-end product journey.

**Blocked by:** 06 — Invitee Claims the Invitation.

**Status:** ready-for-agent

- [ ] Requests require service, preferred start, IANA timezone, and a bounded optional message.
- [ ] Preferred time is stored consistently in UTC and new requests remain pending.
- [ ] Per-Student idempotency prevents duplicate requests while preserving safe retries.
- [ ] Students cannot access another Student's requests and the Tutor can view all business requests.
- [ ] Playwright covers landing through Tutor visibility; black-box tests cover validation, ownership, CSRF, and idempotency.
