# Secure Invite-Only Tutoring Platform

Status: ready-for-agent

## Problem Statement

An independent Tutor needs one secure, coherent product for acquiring Students and
eventually managing scheduling, lesson information, and payment. Today there is no
application foundation, so even the smallest useful journey cannot be exercised from a
clean checkout. The initial product must prove a thin path from a public landing page
through a personalized Invitation, Invitation Claim, and Session Request without
prematurely building a marketplace, multi-tenant SaaS architecture, or external-service
integrations.

Security cannot be postponed until after feature delivery. Invitations, authentication
tokens, private Tutor content, Student identity, and future payment information create
meaningful trust boundaries from the first schema and endpoint. The product therefore
needs secure defaults, explicit authorization, deterministic database migrations, and
repeatable browser/API verification while remaining as simple as a single-Tutor pilot
allows.

## Solution

Build a single-origin application monorepo with a React/TypeScript/Bun/Vite frontend
and a FastAPI/SQLite backend. The required three-day journey is:

`landing page -> personalized Invitation -> Invitation Claim -> Session Request`

The Tutor bootstraps the only privileged account and creates Invitations for known
Invitees. Each Invitation is bound to one email address, keeps Private Tutor Notes
separate from the Shared Personal Message, and is reached through a hashed, expiring
token. The Invitee verifies the bound identity through a short-lived passwordless link,
claims the Invitation, receives a secure server-side Student Session, and submits a
pending Session Request. The Tutor can view that request.

The repository supplies public sanitized health/readiness probes, explicit migrations,
locked dependencies, security gates, and one Playwright command that owns isolated test
state plus both application processes. Payment, confirmed Booking, calendar sync,
reminders, and other broader capabilities remain backlog work that may begin only after
the required path is complete and secure.

## User Stories

1. As a Prospect, I want to view a public landing page, so that I can understand the Tutor's offer.
2. As a Prospect, I want public pages to load without an account, so that evaluating the Tutor has minimal friction.
3. As a Tutor, I want exactly one privileged account, so that the pilot does not expose an unnecessary registration surface.
4. As a Tutor, I want to bootstrap my account through a repository command, so that no default privileged credentials exist.
5. As a Tutor, I want passwordless authentication, so that I do not need another password to secure and maintain.
6. As a Tutor, I want to create an Invitation for a known Invitee, so that onboarding begins from an intentional relationship.
7. As a Tutor, I want to bind an Invitation to a normalized email address, so that only the intended identity can claim it.
8. As a Tutor, I want to correct an Invitation email before claim, so that a typo does not require unsafe identity substitution.
9. As a Tutor, I want to add a Shared Personal Message, so that the Invitee receives relevant welcoming context.
10. As a Tutor, I want Private Tutor Notes stored separately, so that internal context cannot leak to the Invitee or Student.
11. As a Tutor, I want an active Invitation to expire after seven days, so that forgotten links do not remain valid indefinitely.
12. As a Tutor, I want to revoke an active Invitation, so that I can stop onboarding when circumstances change.
13. As a Tutor, I want to regenerate an Invitation, so that a suspected or lost token can be replaced safely.
14. As an Invitee, I want an opaque personal link, so that my identity and discount authority do not appear in URL parameters.
15. As an Invitee, I want to see the Shared Personal Message, so that the setup page feels intentionally personalized.
16. As an Invitee, I want to edit my display name, so that I can correct how the product addresses me.
17. As an Invitee, I want the bound email to remain immutable, so that editing profile data cannot bypass identity verification.
18. As an Invitee, I want expired, revoked, claimed, and invalid links to fail safely, so that token state is predictable without disclosing private details.
19. As an Invitee, I want to request a passwordless link without learning whether another account exists, so that authentication does not enable account enumeration.
20. As an Invitee, I want a passwordless link valid for 15 minutes and one use, so that exposure has a narrow replay window.
21. As an Invitee, I want opening a passwordless link to show confirmation before mutation, so that mail scanners cannot authenticate me automatically.
22. As an Invitee, I want claiming to be atomic, so that concurrent attempts cannot associate my Invitation with multiple accounts.
23. As an Invitee, I want successful verification to create my Student account and Student Session, so that I can continue without another email on every visit.
24. As a Student, I want my Student Session to survive ordinary return visits, so that the product remains convenient.
25. As a Student, I want to log out and revoke my current Student Session, so that I can end access from a device.
26. As a Student, I want my Student Session to expire after inactivity and at an absolute limit, so that old sessions cannot live forever.
27. As a Student, I want access limited to my own records and explicitly shared material, so that another Student's information is never exposed.
28. As a Student, I want to select a service and preferred time, so that I can submit a Session Request.
29. As a Student, I want my timezone recorded and preferred instant normalized to UTC, so that the Tutor and I interpret the time consistently.
30. As a Student, I want to add a short optional message, so that I can provide useful context without submitting unlimited content.
31. As a Student, I want retries to return the same result, so that network repetition cannot create duplicate Session Requests.
32. As a Student, I want a new Session Request to begin pending, so that it is not confused with a confirmed or paid Booking.
33. As a Tutor, I want to view pending Session Requests, so that I can follow up with Students.
34. As a Tutor, I want eventual request transitions to withdrawn, declined, or accepted, so that the lifecycle can grow without redefining Session Request.
35. As a Tutor, I want future acceptance to create a Booking, so that requests and confirmed tutoring sessions remain distinct concepts.
36. As a Tutor, I want Private Tutor Notes and Shared Lesson Notes to be distinct records, so that visibility cannot change accidentally through a toggle.
37. As a Tutor, I want a deletion path for data collected by the current slice, so that unnecessary personal information can be removed.
38. As an operator, I want a public liveness probe with a fixed response, so that process health can be checked without authentication or information leakage.
39. As an operator, I want a public readiness probe, so that database access and schema readiness can be checked independently of process liveness.
40. As an operator, I want stale or inaccessible databases to produce a sanitized not-ready response, so that routing decisions are safe without exposing diagnostics.
41. As an operator, I want migrations applied explicitly before startup, so that the API process never mutates its schema unexpectedly.
42. As a developer, I want a single command to run Playwright with an isolated migrated database and both application processes, so that clean-checkout verification requires no manual services.
43. As a developer, I want locked Bun and Python dependencies, so that local and automated environments resolve the same audited packages.
44. As a developer, I want one typed fail-closed configuration boundary, so that non-development environments cannot inherit insecure local defaults.
45. As a developer, I want frontend requests to use relative API paths on one origin, so that CORS and a second browser trust boundary are unnecessary.
46. As a maintainer, I want deny-by-default authorization and explicit public response models, so that adding fields cannot silently expose private data.
47. As a maintainer, I want unsafe cookie-authenticated requests protected by same-origin validation and CSRF tokens, so that another site cannot submit mutations as a Student or Tutor.
48. As a maintainer, I want authentication rate limits by normalized email and IP, so that abuse is constrained without relying on account existence.
49. As a maintainer, I want safe API errors and allowlisted logs, so that tokens, personal data, and user content do not enter responses or logs.
50. As a maintainer, I want browser security headers, dependency audits, secret scanning, tests, types, linting, builds, and E2E gates, so that security is part of completion.

## Implementation Decisions

- The repository is the product application monorepo. It owns frontend, backend,
  end-to-end harness, and product documentation; the external Gauntlet ledger owns
  accountability and grading.
- Application code has separate frontend, backend, and E2E boundaries. Root package
  configuration provides orchestration only.
- The frontend uses React, TypeScript, Bun, and Vite. The backend uses FastAPI and
  SQLite.
- Browser and API use one origin. Frontend calls relative `/api/*` routes; Vite proxies
  those routes locally; FastAPI does not enable CORS.
- Python dependencies use `uv` with a committed lock and locked synchronization.
  Frontend dependencies use Bun with a committed lock and frozen automated installs.
- Backend configuration uses one typed settings boundary. Local environment files are
  ignored; an example lists names and non-secret placeholders. Non-development startup
  fails when required settings are missing or insecure.
- Persistence uses synchronous SQLAlchemy 2.x. Alembic is the sole schema authority.
- Development may default to an ignored local SQLite database. E2E always supplies a
  temporary database. Non-development environments explicitly supply the database URL.
  Database files beneath tracked or frontend-served locations are rejected.
- The API process never applies migrations. Orchestration applies the latest Alembic
  revision before launch, while stale schema state leaves the process alive but not ready.
- `GET /api/health` is public liveness only. It returns HTTP 200 and
  `{"status":"ok"}` whenever FastAPI is serving and never queries SQLite.
- `GET /api/ready` is public readiness. It returns HTTP 200 and
  `{"status":"ready"}` only when SQLite is reachable and at the expected Alembic head.
  Database failure returns HTTP 503 with
  `{"status":"not_ready","reason":"database"}`; schema mismatch returns the same
  status with reason `schema`.
- Probe responses expose no software versions, paths, exceptions, migration identifiers,
  or database details. Internal diagnostics remain in sanitized server logs.
- The product is invite-only. Public Tutor registration and Student signup detached
  from an Invitation do not exist. A repository command creates exactly one Tutor.
- An Invitation uses `draft -> active -> claimed`, with `revoked` and `expired` terminal
  alternatives for an active record.
- Invitations bind to normalized email addresses. Invitees may edit display names but
  cannot replace the bound email. Raw tokens are delivered once, stored only as hashes,
  expire after seven days, and are permanently invalidated by claim, revocation,
  expiration, or regeneration.
- Invitation Claim is atomic and requires verification of the bound address. It records
  account association independently of payment.
- Private Tutor Notes and Shared Personal Messages are separate fields and response
  boundaries. Public and Student-facing responses are explicit allowlists.
- Magic-link tokens are random, hashed at rest, single-use, and expire after 15 minutes.
  GET renders confirmation and POST consumes the token. Responses are enumeration-safe.
- Initial magic-link request ceilings are five per normalized email per hour and twenty
  per IP per hour.
- Authentication creates an opaque server-side Student Session. Production cookies use
  a host-only `__Host-` name with Secure, HttpOnly, SameSite=Lax, Path=/, and no Domain.
  Authentication rotates session identity; logout revokes it server-side.
- Student Sessions expire after 30 days of inactivity and 90 days absolutely. Activity
  may extend inactivity expiration but never the absolute deadline.
- Authorization is deny-by-default. Tutor access covers the single business; Student
  access is constrained by record ownership and explicit sharing.
- Cookie-authenticated unsafe requests require a valid same-origin Origin and CSRF token.
- Session Request requires service, preferred start, and IANA timezone. Preferred time
  is stored in UTC. Optional plain text is limited to 1,000 characters.
- Session Request uses `pending -> withdrawn | declined | accepted`. Required delivery
  includes creation and Tutor visibility. Other transitions remain backlog; acceptance
  will create a Booking.
- Session Request creation requires an idempotency key unique per Student.
- Private Tutor Notes and Shared Lesson Notes are distinct record types, never one
  record with mutable visibility.
- Collect only data required by the active slice. Tutor-driven deletion precedes
  self-service deletion. Financial retention rules must be defined before payment data.
- Browser responses use a restrictive same-origin content security policy, deny
  framing, disable MIME sniffing, use a strict referrer policy, and disable unused
  browser permissions.
- API errors contain a stable code, safe message, and request ID. Validation errors may
  name fields but never echo submitted values.
- Application logs allow only event name, request ID, route template, method, status,
  duration, and necessary opaque internal identifiers. They exclude raw URLs, query
  strings, bodies, cookies, authorization data, tokens, emails, notes, and payment data.
- Security is a completion gate. Each slice defines trust/data boundaries, enforces
  authorization, sanitizes output, covers negative behavior, and passes automated checks.
- The root E2E command creates a temporary SQLite database, applies migrations, starts
  FastAPI, waits for readiness, starts Vite, runs Playwright, tears down both processes,
  and removes test state. It never reuses development or production data.

## Testing Decisions

- Tests assert externally observable behavior rather than private implementation,
  internal call ordering, ORM structure, or framework-specific details.
- The primary seam is one Playwright critical journey: public landing page, Tutor-created
  Invitation, Invitee setup, passwordless Invitation Claim, Student Session Request,
  and Tutor visibility of the pending request.
- The second seam is black-box HTTP testing against the FastAPI application. It covers
  health/readiness, authentication, authorization, CSRF, Invitation lifecycle, token
  expiration and reuse, rate limits, idempotency, sanitized errors, and private-field
  exclusion.
- Readiness tests cover healthy schema, inaccessible database, missing/outdated schema,
  correct status codes, exact safe response shapes, and absence of internal diagnostics.
- Invitation tests cover draft activation, seven-day expiration, revocation,
  regeneration, invalid tokens, email binding, editable display name, atomic claim,
  and inability to claim twice or from another verified address.
- Authentication tests cover enumeration-safe responses, rate limits, 15-minute expiry,
  hashing, one-time use, confirmation-before-consumption, session rotation, logout,
  inactivity expiration, and absolute expiration.
- Authorization tests attempt cross-Student access, anonymous privileged access, private
  note exposure, mass-assignment of private fields, missing/foreign CSRF tokens, and
  invalid Origin headers.
- Session Request tests cover required fields, UTC normalization, IANA timezone,
  message length, initial pending status, per-Student idempotency, and Tutor visibility.
- Browser tests verify security headers at the external response boundary without
  coupling to middleware structure.
- Harness tests prove no pre-running services or persistent test database are required
  and that processes/state are cleaned after success and failure.
- Automated completion includes backend/frontend tests, type checking, linting,
  production builds, Playwright, Bun/Python dependency audits, and secret scanning.
- There is no application-test prior art in the current repository. These two seams are
  intentionally the first and highest-level testing contracts.

## Out of Scope

- Multiple Tutors, organizations, tenants, or a Tutor marketplace.
- Public Tutor registration or open Student signup during the pilot.
- Platform commissions, connected accounts, payouts, or revenue splitting.
- Required deployment, real email delivery, or external network-service availability.
- Required payment collection, discount redemption, confirmed Booking, availability
  computation, calendar synchronization, reminders, rescheduling, or cancellation.
- Required lesson-note UI, file/resource sharing, or self-service account deletion.
- Google sign-in beyond stretch work; Apple and GitHub sign-in.
- Architecture justified only by hypothetical SaaS conversion or scale.
- Visual browser grading.

The out-of-scope product capabilities remain backlog candidates. They may be started
after the required secure journey is complete, but they do not redefine acceptance for
this spec.

## Further Notes

- The required build boundary is the secure repository-only journey, not deployment.
- The first implementation day establishes both application layers, migrations,
  liveness/readiness, a tested landing page, and the clean-checkout Playwright harness.
- Product terminology is intentionally strict: a Session Request is pending; a Booking
  is confirmed and has a payment relationship; a Student Session is authentication.
- Simplicity and security reinforce each other here: single origin, one Tutor, SQLite,
  synchronous persistence, explicit migrations, and two external test seams minimize
  machinery without weakening trust boundaries.
