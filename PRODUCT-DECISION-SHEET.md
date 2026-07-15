# Product Decision Sheet

**Status:** Accepted in full on 2026-07-15.

1. **Invitee name** — May an invitee edit their prefilled display name while the bound
   email remains immutable? **Decision: yes.**
2. **Magic links** — Should tokens be random, hashed at rest, single-use, and valid for
   15 minutes, with `GET` showing a confirmation page and `POST` consuming the token so
   link scanners cannot sign in? **Decision: yes.**
3. **Authentication abuse controls** — Should auth responses avoid account enumeration
   and enforce limits by both normalized email and IP? Initial ceiling: five link
   requests per email per hour and twenty per IP per hour. **Decision: yes.**
4. **CSRF** — Should every cookie-authenticated state-changing request require a valid
   same-origin `Origin` plus a CSRF token? **Decision: yes.**
5. **Session Request fields** — Require service, preferred start, and IANA timezone;
   store the instant in UTC and allow an optional plain-text message capped at 1,000
   characters. **Decision: yes.**
6. **Session Request lifecycle** — Use `pending -> withdrawn | declined | accepted`;
   the pilot needs create and tutor-view only, while the other transitions remain
   backlog. Future acceptance creates a Booking. **Decision: yes.**
7. **Duplicate submissions** — Require an idempotency key for Session Request creation
   and enforce it per student in SQLite so retries cannot create duplicates.
   **Decision: yes.**
8. **Lesson-note visibility** — Model Private Tutor Notes and Shared Lesson Notes as
   distinct record types; never toggle one record between private and shared.
   **Decision: yes.**
9. **Data minimization** — Collect only fields needed by the current slice, provide the
   tutor a deletion path before adding self-service deletion, and define legal/financial
   retention only when payments arrive. **Decision: yes.**
10. **Browser protections** — Send a restrictive same-origin CSP, deny framing, disable
    MIME sniffing, use a strict referrer policy, and disable unused browser permissions.
    **Decision: yes.**
11. **API errors** — Return only a stable error code, safe message, and request ID;
    validation errors identify fields but never echo submitted values. **Decision: yes.**
12. **Automated security gates** — Require tests, type checks, linting, production
    builds, Playwright, dependency audits for Bun/Python, and secret scanning before a
    slice is complete. **Decision: yes.**
