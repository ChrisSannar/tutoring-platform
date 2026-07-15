# Product Grilling: Single-Tutor Platform (2026-07-15 through 2026-07-17)

*Product scope for a three-day build used to test the Gauntlet's adaptive
accountability loop.*

## Status

Completed for the frozen three-day slice on 2026-07-15. Reopen backlog decisions only
as their features are scheduled; do not mix them into accountability-system design.

## Current implementation constraints

- This repository is the product application monorepo; the Gauntlet ledger and its
  accountability machinery remain external.
- Application code is divided into `frontend/`, `backend/`, and `e2e/`. The root
  `package.json` owns orchestration commands only.
- The product frontend uses React, TypeScript, Bun, and Vite.
- The product backend uses FastAPI and SQLite.
- The browser and API share one origin. Frontend code calls relative `/api/*` paths;
  Vite proxies `/api` to FastAPI during development and E2E; FastAPI enables no CORS
  middleware.
- Python dependencies use `uv`, a committed `uv.lock`, and locked installs through
  `uv sync --locked`. Frontend dependencies use Bun with its committed lockfile and
  frozen installs in automated environments.
- Backend configuration flows through one typed `pydantic-settings` object. Local
  `.env` files are ignored; a committed `.env.example` contains variable names and
  non-secret placeholders only. Non-development startup fails closed when required
  settings are missing or insecure instead of falling back to development values.
- Persistence uses synchronous SQLAlchemy 2.x. Alembic is the schema authority, and
  readiness compares the database's current Alembic revision with the application's
  expected head revision.
- Development defaults to an ignored `backend/var/tutoring.db`. E2E always supplies a
  temporary database, and every non-development environment must explicitly provide
  `DATABASE_URL`. Database paths inside tracked or frontend-served directories are
  rejected.
- The FastAPI process never applies migrations or otherwise modifies the schema during
  startup. Orchestration commands apply `alembic upgrade head` before launching the
  server; a stale schema makes the application not ready.
- The Day 1 backend boundary includes `GET /api/health`, a liveness-only check that
  returns HTTP 200 with `{"status":"ok"}` whenever FastAPI is serving. It does not
  query SQLite.
- `GET /api/ready` returns HTTP 200 with `{"status":"ready"}` only when SQLite is
  reachable and the schema is at the expected migration revision. Otherwise it returns
  HTTP 503 with `{"status":"not_ready","reason":"database"}` or
  `{"status":"not_ready","reason":"schema"}`. Internal diagnostics are logged, not
  exposed in the response.
- `GET /api/health` and `GET /api/ready` are deliberately public and unauthenticated
  infrastructure probes. Their fixed response shapes expose no versions, filesystem
  paths, exception text, migration identifiers, or database details.
- After dependencies are installed, one root command, `bun run test:e2e`, owns the
  complete Playwright lifecycle: create an isolated temporary SQLite database, apply
  migrations, start FastAPI, wait for `/api/ready`, start Vite, run Playwright, stop
  both processes, and remove test state. It requires no manually running service and
  never reuses development or production data.
- Development prioritizes security before feature breadth while choosing the simplest
  design that satisfies the security completion gate. Complexity justified only by
  hypothetical scale is rejected.

## Security completion gate

A feature slice is incomplete until it has:

- explicit public/private data and trust boundaries;
- deny-by-default authorization for every non-public operation;
- sanitized responses and logs containing no secrets or unnecessary personal data;
- negative-path tests for unauthorized, invalid, and abusive input; and
- dependency and security-sensitive configuration checks in CI.

This gate applies to the finite daily boundary as well as optional backlog work.

## Logging boundary

Application logging uses an explicit allowlist: event name, request ID, route template,
HTTP method, response status, and duration. Normal logs never contain raw URLs, query
strings, request or response bodies, cookies, authorization headers, invitation or
authentication tokens, email addresses, lesson notes, or payment details. Security
events may reference internal opaque record identifiers, but not sensitive values or
user-authored content.

## Product intent

Give one independent tutor a coherent operating system for acquiring students and
running lessons. A prospective student should be able to understand the offer and
book a service and available time, pay, and receive an immediately confirmed session.
An active student should be able to manage sessions and use the lesson material the
tutor shares with them.

The reward for efficient work is more functioning product. The task backlog may remain
open-ended, while each day retains a finite required boundary (ADR 0016).

The pilot has a 30-hour envelope. Intended capabilities below are backlog candidates;
the adaptive planner must prefer thin end-to-end value over incomplete breadth.

## Actors

- **Tutor**: the single business owner. Controls services, availability, sessions,
  lesson records, resources, and payment configuration.
- **Prospect**: a person evaluating the tutor who has not established an ongoing
  student relationship.
- **Invitee**: a known prospect for whom the tutor created a personalized invitation,
  but who has not yet claimed it or created an account.
- **Student**: a person with a tutoring relationship who can manage their sessions and
  access material shared with them.
- **Calendar provider**: external source and destination for availability and session
  events.
- **Payment provider**: external system that authorizes and records payment.
- **Accountability system**: assigns daily work and grades frozen evidence; it is not a
  tutoring-platform user.

## Intended capabilities

- Public landing page for prospective students.
- Tutor admin flow for creating a personalized invitation for a known prospect.
- Opaque personal invitation link with a pre-account setup page and an optional
  invitation-bound, one-time discount.
- Invitation claim through signup/authentication, producing the student's account and
  preserving the intended booking context.
- Session scheduling with calendar synchronization.
- Rescheduling and cancellation.
- Lesson notes shared with the appropriate student.
- File and resource sharing.
- Lesson reminders.
- Payment collection and payment-state visibility.
- Pending session requests that let an invited student propose a service and preferred
  time before the full booking/payment workflow exists.

## Repository-only evidence constraint

The product is not deployed during this run. The controller clones the frozen product
commit and runs unit, integration, type, build, and local Playwright checks there.
Real email, calendar, payment, and network-service availability are not grading gates.

## Explicit pilot non-goals

- Multiple tutor organizations or tenant isolation.
- Tutor marketplace, tutor discovery, or matching.
- Platform commissions, connected-account payouts, or tutor revenue splitting.
- Architecture whose only justification is a hypothetical later SaaS conversion.

## Decision status

The compact product/security decision sheet was accepted in full on 2026-07-15. See
[`PRODUCT-DECISION-SHEET.md`](PRODUCT-DECISION-SHEET.md). No unresolved decision blocks
the frozen three-day slice.

## Session request and future booking

For the three-day slice, an invited student submits a **Session Request** containing a
service and preferred time. It remains pending for the tutor and is not a confirmed or
paid booking. Tutor approval, immediate confirmation, payment, calendar sync, and
reminders remain backlog candidates that may be implemented if time permits.

The intended future direct-booking journey remains: a public prospect chooses a service
and available time, pays, and receives an immediately confirmed **Booking**. Calendar
synchronization and reminder scheduling follow that confirmed booking.

## Invitation lifecycle

The tutor may create a personalized invitation before an account exists. The system
issues an opaque link whose token refers to server-side invitation data; personally
identifying information and discount authority do not live in URL parameters. The
invitation stores **private tutor notes** separately from a **shared personal message**.
Private notes are never returned by invitee or student endpoints; the shared message is
deliberately rendered on the setup page. This is an authorization boundary, not merely
a presentation choice. The invitation has an explicit lifecycle:

`draft -> active -> claimed`

An active invitation may also become `revoked` or `expired`. Claiming it requires
verified signup/authentication, permanently associates the invitation with that one
student account, and records the claim independently of payment.

Each invitation is bound to a normalized email address and may be claimed only after
that same address is verified. The tutor may correct the address before claim; the
invitee cannot replace it during signup, but may edit their prefilled display name. Raw
invitation tokens appear only in delivered links and are stored as hashes. An active
link expires after seven days. Claiming, revoking, expiring, or regenerating an
invitation permanently invalidates the old token, and claim is atomic so concurrent
attempts cannot associate two accounts.

Any invitation-bound discount remains available through failed or abandoned checkout
attempts. It is redeemed only by the first successful payment and records that payment
as evidence. A claimed invitation cannot be claimed by another account.

## Student authentication and sessions

Students verify their identity through an emailed magic link or one-time code. A
successful verification creates an opaque server-side session; subsequent visits do
not require another email while that session remains valid. Google sign-in is stretch
work. Apple and GitHub sign-in are outside the pilot's required boundary.

The product is invite-only during the pilot. There is no public tutor registration or
public student signup detached from an invitation. Exactly one tutor account is created
through a repository-local bootstrap command and uses the same passwordless
authentication mechanism as students. Opening registration is future product work.

Magic-link tokens are random, hashed at rest, single-use, and valid for 15 minutes. A
`GET` displays a confirmation page; a state-changing `POST` consumes the token so link
scanners cannot authenticate a user. Responses do not reveal whether an account exists.
Link requests are initially limited to five per normalized email per hour and twenty
per IP per hour.

Production serves authentication only over HTTPS. HTTP redirects to HTTPS, and the
session identifier uses a host-only cookie with a `__Host-` name, `Secure`, `HttpOnly`,
`SameSite=Lax`, and `Path=/`; it has no `Domain` attribute. The application rotates the
session after authentication and supports logout and server-side revocation.

The session expires after 30 days without activity and has a 90-day absolute lifetime.
Normal authenticated use may extend the inactivity deadline but never the absolute
deadline.

## Authorization

Authorization is deny-by-default. The tutor may manage all records belonging to the
single tutoring business. A student may access only their own account, session
requests, sessions, and material explicitly shared with them. Public invitation
responses use explicit allowlisted response models; private tutor fields are excluded
at the serialization boundary rather than hidden only in the interface.

Every cookie-authenticated state-changing request requires both a valid same-origin
`Origin` and a CSRF token.

## Session requests

A Session Request requires a service, preferred start, and IANA timezone. The preferred
instant is stored in UTC; an optional plain-text message is capped at 1,000 characters.
Its lifecycle is `pending -> withdrawn | declined | accepted`. The pilot requires only
creation and tutor visibility; the remaining transitions stay on the backlog, and
future acceptance creates a Booking.

Creation requires an idempotency key that is unique per student so retries cannot
create duplicate requests.

## Notes and data stewardship

Private Tutor Notes and Shared Lesson Notes are distinct record types; a single record
cannot be toggled between private and shared. The product collects only data needed by
the current slice. Tutor-driven deletion precedes self-service deletion, and retention
requirements will be defined before payment or regulated financial data is stored.

## HTTP and automated security controls

Browser responses use a restrictive same-origin content security policy, deny framing,
disable MIME sniffing, use a strict referrer policy, and disable unused browser
permissions. API errors contain only a stable code, safe message, and request ID;
validation errors identify fields without echoing submitted values.

A slice must pass tests, type checks, linting, production builds, Playwright,
dependency audits for Bun and Python, and secret scanning before it is complete.

## Booking and calendar authority

The tutoring platform is authoritative for a session's service, student, time, payment
relationship, and lifecycle state. Booking, rescheduling, and cancellation commands go
through the platform and then synchronize to the configured calendar provider.

The calendar provider contributes busy-time constraints when the platform computes
availability and stores a mirrored event for each confirmed session. Direct changes to
that mirrored event do not silently change the platform booking. The synchronization
process detects the mismatch, records it as drift, and surfaces repair work to the
tutor and maintenance backlog.

Calendar writes must be retryable and idempotent. Each booking retains the external
event identifier and synchronization status needed to reconcile failures without
creating duplicate events.

## Cancellation and rescheduling policy

- At least 24 hours before a session, a student may cancel for a full refund or use one
  self-service reschedule.
- Inside 24 hours, the platform does not automatically refund or reschedule; the
  student must contact the tutor.
- The tutor may override the policy from the admin interface.
- Rescheduling retains the original successful payment instead of refunding and
  charging again.
