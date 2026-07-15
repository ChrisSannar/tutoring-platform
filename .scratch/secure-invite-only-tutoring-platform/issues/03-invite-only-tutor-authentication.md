# 03 — Invite-Only Tutor Authentication

**What to build:** The single bootstrapped Tutor can authenticate through a secure development-outbox magic link, retain a server-side session, and log out without exposing public privileged registration.

**Blocked by:** 02 — SQLite Schema Readiness.

**Status:** ready-for-agent

- [ ] A repository command creates exactly one Tutor without default credentials.
- [ ] Magic-link request and confirmation are enumeration-safe, hashed, single-use, and time limited.
- [ ] Rate limits enforce the accepted email and IP ceilings.
- [ ] Session cookies, rotation, expiry, logout, Origin validation, and CSRF follow the spec.
- [ ] Public HTTP behavior and the Tutor browser flow are covered red-first at confirmed seams.
