# 03 — Invite-Only Tutor Authentication

**What to build:** The single bootstrapped Tutor can authenticate through a secure development-outbox magic link, retain a server-side session, and log out without exposing public privileged registration.

**Blocked by:** 02 — SQLite Schema Readiness.

**Status:** resolved

- [x] A repository command creates exactly one Tutor without default credentials.
- [x] Magic-link request and confirmation are enumeration-safe, hashed, single-use, and time limited.
- [x] Rate limits enforce the accepted email and IP ceilings.
- [x] Session cookies, rotation, expiry, logout, Origin validation, and CSRF follow the spec.
- [x] Public HTTP behavior and the Tutor browser flow are covered red-first at confirmed seams.

## Answer

Implemented a repository-owned single-Tutor bootstrap command, development-outbox
passwordless authentication, hashed one-time magic links, email/IP rate limits, and
server-side Tutor sessions with secure cookie policy, rotation, inactivity and absolute
expiry, same-origin CSRF-protected logout, and server-side revocation. Black-box HTTP
tests cover the security boundary, while Playwright covers sign-in, an ordinary return
visit, and logout through the visible Tutor flow. `bun run test` passes with 18 backend
tests and 4 Playwright tests.
