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

## Original pilot capabilities (historical)

This section records the July 15 pilot framing and is not the current implementation
source for the post-pilot flow settled below.

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

The product flow was reopened on 2026-07-16 for the next application phase. Decisions
in this new grilling session are recorded below. Shared understanding was confirmed on
2026-07-17; `IMPLEMENTATION-ASSESSMENT.md` maps the accepted flow to the live codebase.

## Public inquiry flow

Anyone may submit an **Inquiry** from the public landing page using an email address
and required contextual message. An Inquiry grants no account or application access.
The Tutor manages Inquiries from the privileged dashboard and may create a separate
Invitation to send to the Prospect.

Submitting the public form stores a New Inquiry for the Tutor Dashboard and shows the
Prospect an on-page confirmation. The first version sends no Tutor notification email;
the dashboard is the sole delivery channel.

The public Inquiry endpoint validates normalized email, requires a contextual message
of at most 2,000 plain-text characters, and initially allows five submissions per hashed
IP per hour. It returns safe errors and never renders Inquiry content as raw HTML.
CAPTCHA is deferred unless observed abuse justifies it.

The landing header shows **Log In** when no valid application session exists and
**Dashboard** when one does. Dashboard routes the current Tutor or Student directly to
their role-appropriate dashboard; an absent or expired session falls back to Log In.

The landing hero has one primary call to action, **Request tutoring**, which opens the
email-and-message Inquiry modal. It never labels the action Sign up because access still
requires a Tutor-created Invitation.

The first landing release stays deliberately tight: Request tutoring is the only
primary button, while the small role-aware Log In/Dashboard action remains the sole
header utility.

The privileged interface is the **Tutor Dashboard**, not an Admin Dashboard. A Prospect
becomes an Invitee when the Tutor creates an Invitation and becomes a Student only
after claiming it; the Student list therefore never contains unclaimed Invitees.

Creating an Invitation from an Inquiry produces a link for the Tutor to deliver
manually. The product does not compose or send the personalized invitation email; the
Tutor writes that message through their normal email workflow.

The Tutor performs this through one **Create Invitation Link** action. The application
atomically creates an active Invitation bound to the Inquiry email, generates its
seven-day single-use link, keeps it copyable by the authenticated Tutor until claim,
and marks the Inquiry as invited. The Tutor does not manage a separate draft or
activation step and may regenerate or revoke the Invitation Link.

The active Inquiry list distinguishes **New** Inquiries from **Invited** Inquiries. New
Inquiries offer Create Invitation Link; Invited Inquiries expose the applicable link
management actions. Claiming the linked Invitation removes the Inquiry from the active
list because the person now appears in the Student list. The Tutor may archive spam or
an Inquiry they will not pursue, removing it from the active list without granting
access.

Repeated public submissions create separate Inquiry records; the low-volume release
does not merge messages by email. Archiving hides an Inquiry but retains it, while a
separate confirmed Delete action permanently removes it.

The Tutor Dashboard also offers **Create Invitation Link manually** independently of
the Inquiry list. The Tutor enters only an email; the application creates the same
active seven-day Invitation and keeps its link available to the authenticated Tutor
until claim. The Invitee supplies their display name during account setup. This path
does not create a synthetic Inquiry, and both entry points reuse the same Invitation
Claim behavior.

The manually delivered **Invitation Link** is the only link in first-time onboarding.
It opens account setup, and confirmation atomically claims the Invitation, creates the
Student account, and starts a Student Session. The Invitee does not request or follow
a second authentication link. A returning Student instead requests a short-lived
**Login Link** from the public login flow.

Opening an Invitation Link is observational and never creates an account; automated
email scanners and link previews may open it. The setup page shows the read-only bound
email and editable display name. Only the Invitee's explicit **Create Account** action
consumes the link, claims the Invitation, creates the Student account, starts the
Student Session, and navigates to the Student Dashboard.

Initial account setup collects only an editable display name and the Invitation's
read-only bound email. It does not collect a password, phone number, address, payment
details, timezone, or profile questionnaire; later workflows collect additional data
only when they need it.

## Session request and future booking

For the three-day slice, an invited student submits a **Session Request** containing a
service and preferred time. It remains pending for the tutor and is not a confirmed or
paid booking. Tutor approval, immediate confirmation, payment, calendar sync, and
reminders remain backlog candidates that may be implemented if time permits.

The intended future direct-booking journey remains: a public prospect chooses a service
and available time, pays, and receives an immediately confirmed **Booking**. Calendar
synchronization and reminder scheduling follow that confirmed booking.

For the post-pilot product flow settled on 2026-07-16 and 2026-07-17, direct Booking
supersedes Session Request in the user-facing experience. Promotion, Session Credit
redemption, or successful payment confirms the Booking immediately without Tutor
acceptance. The existing Session Request implementation remains useful only as a source
of ownership, authorization, UTC-storage, idempotency, and Tutor-visibility patterns;
it is not a parallel scheduling path.

## Invitation lifecycle

The Tutor may create an Invitation before an account exists. The system
issues an opaque link whose token refers to server-side invitation data; personally
identifying information and access authority do not live in URL parameters. The Tutor
writes and sends personalized invitation copy through normal email; the setup page
contains only the bound read-only email and editable display name. The Invitation has
an explicit lifecycle:

`created -> opened -> claimed`

A created or opened invitation may instead become `revoked` or `expired`. Opening an
invitation is the first successful load of its personalized setup page; later valid
loads remain `opened`. The transition records the first successful server response, not
proof of human readership, so an automated link scanner may cause it. Opening neither
consumes the token nor changes its expiration. Claiming requires confirmation by the
holder of the active Invitation Link, permanently associates the Invitation with that
one Student account, creates a Student Session, and records the claim independently of
payment. Possession of the manually emailed Invitation Link is the initial proof of
access to the bound email; onboarding does not send a second authentication link.

Each Invitation is bound to a normalized email address. Possession of the manually
emailed Invitation Link is the initial verification of access to that address. The
Tutor may correct the address before claim; the Invitee cannot replace it during setup
but may enter their display name.
Creation stores a token hash for lookup plus a separately encrypted copy that only the
authenticated Tutor may retrieve. The encrypted copy is erased when the Invitation is
claimed, revoked, expired, or regenerated; regeneration replaces and invalidates the
old token. A created or opened Invitation expires seven days after creation regardless
of whether or how often it is opened. The deadline is authoritative as soon as it
passes. The first subsequent token lookup, Tutor inspection, claim, or mutation
atomically persists `expired`; no background expiration scheduler is required. Claim
is atomic so concurrent attempts cannot associate two accounts.

The Tutor may revoke a `created` or `opened` Invitation. Revocation preserves the
record, immediately invalidates its token, and is idempotent: retrying revocation of an
already `revoked` Invitation succeeds with the same state. Revoking a `claimed` or
`expired` Invitation is an invalid transition and returns a sanitized conflict.

Each Invitation persists one current status plus lifecycle evidence. `created_at` is
required; `first_opened_at`, `claimed_at`, `expired_at`, and `revoked_at` are nullable
and written when their corresponding transition occurs. `claimed_account_id` is
populated only by claim. Each state transition and its timestamp or account association
is one atomic database change; the pilot does not require an event-history table.

A claimed Invitation cannot be claimed by another account. The First Session Promotion
belongs to the resulting Student account rather than to checkout data on the Invitation.

## Student authentication and sessions

An Invitee claims their account using the Tutor-delivered Invitation Link. A returning
Student requests an emailed Login Link; successfully confirming either kind of link
creates an opaque server-side session, and subsequent visits do not require another
email while that session remains valid. Google sign-in is stretch work. Apple and
GitHub sign-in are outside the pilot's required boundary.

The product is invite-only during the pilot. There is no public tutor registration or
public student signup detached from an invitation. Exactly one tutor account is created
through a repository-local bootstrap command and uses the same passwordless
authentication mechanism as students. Opening registration is future product work.

Login Link tokens are random, hashed at rest, single-use, and valid for 15 minutes. A
`GET` displays a confirmation page; a state-changing `POST` consumes the token so link
scanners cannot authenticate a user. Responses do not reveal whether an account exists.
Link requests are initially limited to five per normalized email per hour and twenty
per IP per hour. Invitation Links retain their separate seven-day lifetime and are
consumed only when account setup is confirmed, not when their setup page is opened.

Tutor and Student accounts share one return-login flow. The public **Log In** action
opens an email form and always returns the same generic accepted response. Its Login
Link opens one role-neutral confirmation route; successful confirmation starts a
session and redirects the Tutor to the Tutor Dashboard or the Student to the Student
Dashboard according to the authenticated account role.

Automated Login Link email delivery is deliberately deferred. A returning Student's
eligible submission creates a **Login Request** in the Tutor Dashboard while the public
response remains generic. The Tutor explicitly generates the 15-minute Login Link,
starting its lifetime at that moment, copies it, and sends it through normal email.
Used, expired, or dismissed requests leave the active queue. A repository command may
generate the Tutor's own short-lived Login Link when the Tutor is logged out, avoiding
a dependency on the very dashboard being accessed. This manual boundary is accepted as
temporary until the product justifies a mail provider.

Production serves authentication only over HTTPS. HTTP redirects to HTTPS, and the
session identifier uses a host-only cookie with a `__Host-` name, `Secure`, `HttpOnly`,
`SameSite=Lax`, and `Path=/`; it has no `Domain` attribute. The application rotates the
session after authentication and supports logout and server-side revocation.

The session expires after 30 days without activity and has a 90-day absolute lifetime.
Normal authenticated use may extend the inactivity deadline but never the absolute
deadline.

## Authorization

Authorization is deny-by-default. The Tutor may manage all records belonging to the
single tutoring business. A Student may access only their own account, Bookings,
funding status, and material explicitly shared with them. Public Invitation
responses use explicit allowlisted response models; private tutor fields are excluded
at the serialization boundary rather than hidden only in the interface.

Every cookie-authenticated state-changing request requires both a valid same-origin
`Origin` and a CSRF token.

## Notes and data stewardship

Private Tutor Notes and Shared Lesson Notes are distinct record types; a single record
cannot be toggled between private and shared. The product collects only data needed by
the current slice. Tutor-driven deletion precedes self-service deletion, and retention
requirements will be defined before payment or regulated financial data is stored.

The Student Dashboard has one responsive two-panel layout: Shared Lesson Notes on the
left and the weekly calendar on the right at desktop widths, with the calendar followed
by notes on smaller screens. Welcome guidance sits above the panels and is not stored
as a Lesson Note. Shared Lesson Notes appear in one accordion; the calendar does not
duplicate a second past-notes list.

Every Shared Lesson Note belongs to exactly one past Booking and contains a Tutor-authored
title plus Markdown content. Its accordion header uses the Booking's fixed tutoring
date; there is no separate editable note date. The Student may download the same
content as a generated `.md` file.

A non-canceled Booking becomes a **Past Booking** automatically when its 60-minute end
passes. The Tutor may then create a Lesson Note Draft for it. The first release has no
separate completion action, attendance status, or no-show state, and canceled Bookings
cannot receive Lesson Notes.

The Tutor may save a **Lesson Note Draft** that remains Tutor-only. Explicitly
publishing it makes the note visible to the Student as a Shared Lesson Note. Later
edits update that same shared record and its download; deletion requires confirmation
and removes Student access. A draft never becomes student-visible merely because it
was saved.

The Student Dashboard renders published Markdown as sanitized formatted content in a
bounded, scrollable accordion panel. Raw HTML is disabled or sanitized. Downloading a
note returns the original Markdown source as a `.md` file with a stable filename based
on the session date and note title.

Lesson Note Markdown is stored as plain text and limited to 100 KB per note. File
attachments are deferred.

## HTTP and automated security controls

Browser responses use a restrictive same-origin content security policy, deny framing,
disable MIME sniffing, use a strict referrer policy, and disable unused browser
permissions. API errors contain only a stable code, safe message, and request ID;
validation errors identify fields without echoing submitted values.

A slice must pass tests, type checks, linting, production builds, Playwright,
dependency audits for Bun and Python, and secret scanning before it is complete.

## Booking and calendar authority

The tutoring platform is authoritative for a Booking's Student, time, funding,
Meeting Details, and lifecycle state. Booking, rescheduling, and cancellation commands
go through the platform.

Students may select time only inside Tutor-defined **Availability Windows**. Existing
Bookings and blocked time remove availability; ordinary blank calendar space outside
an Availability Window is unavailable and cannot be selected.

Student self-scheduling permits Bookable Slots from 24 hours through eight weeks in the
future. Tutor Overrides may schedule outside both limits.

The first scheduling version uses one 60-minute duration for every Booking. Multiple
session types and durations are deferred.

The first release has no service catalog or service selector. A Student may add one
optional plain-text **Booking Focus** of at most 500 characters describing what they
want to work on.

A Student-created Booking is confirmed only after the application atomically redeems
one available Session Credit or records successful payment. Selecting a Bookable Slot
only prepares the confirmation modal; if neither funding path completes, no Booking is
created and the slot remains available. Tutor-created overrides are a separate policy.

Paid Bookings use Stripe-hosted Checkout rather than an application-hosted card form.
The server creates Checkout from Tutor-owned pricing configuration and never accepts a
price from the browser. A verified Stripe webhook performs idempotent payment
fulfillment and Booking confirmation; the browser success redirect alone is not proof
of payment. The charged amount and funding evidence are snapshotted so later pricing
changes cannot rewrite Booking history.

The first version has one global Tutor-configured **Session Price** in USD for every
60-minute paid Booking. It is stored as integer cents. Price changes affect only future
Checkout Sessions; existing payments and Bookings retain their original amount.

Starting Stripe Checkout atomically creates a 30-minute **Slot Hold** so competing
Students cannot select the same Bookable Slot. Successful payment converts the hold
into a Booking; abandoned or expired Checkout releases it. Session Credit and First
Session Promotion bookings confirm atomically and do not need a hold.

One **Session Credit** funds one 60-minute Booking. The Tutor initially owns all credit
grants and balance adjustments. Paying during scheduling funds only the selected
Booking and does not add a general credit balance; Student-purchased credits, bundles,
expiration, and wallet behavior are deferred.

Every Session Credit grant, redemption, restoration, freeze, and deduction appends to
an immutable **Credit Ledger**. Tutor grants, deductions, and funding overrides require
a short reason; balances are derived from ledger entries rather than edited without
history.

The Tutor may create a **Complimentary Booking** for a Student without payment or
Session Credit redemption. Complimentary funding is recorded explicitly and does not
silently alter the Student's credit balance or First Session Promotion.

Every newly claimed Student receives a one-time **First Session Promotion**. It applies
automatically to the Student's earliest eligible Booking, making that Booking free;
the Student cannot pay instead to save the promotion for later. Promotional funding is
recorded separately from ordinary Tutor-granted Session Credits.

Canceling or rescheduling a promoted Booking at least 24 hours before its start restores
the First Session Promotion; canceling inside 24 hours forfeits it under the same rule
as an ordinary Session Credit. An explicit **Tutor Override** may change Booking details
without penalizing the Student. Tutor-initiated changes preserve payment, Session
Credit, or promotional funding by default and never trigger automatic forfeiture.

Each Availability Window is partitioned into consecutive 60-minute Bookable Slots
anchored at the window's start. Students select one whole slot and cannot choose
arbitrary minute ranges; a `4:30–7:30` window therefore yields `4:30`, `5:30`, and
`6:30` starts when all three remain free.

Availability uses recurring weekly Availability Windows plus date-specific **Blocked
Time** for holidays, appointments, or time off. Blocked Time removes overlapping
Bookable Slots without rewriting the recurring schedule.

The Tutor manages both kinds of availability directly from the weekly Tutor calendar.
Creating or selecting calendar time opens a small modal for a recurring Availability
Window or one-off Blocked Time; existing entries may be edited or deleted there.

The local-client release uses one Tutor-configured **Tutor Timezone** for every
Availability Window, Bookable Slot, Booking, calendar display, and Calendar Export.
Student-local conversion and timezone selection are deferred until the business serves
clients outside the Tutor's timezone.

The Student calendar exposes full information only for that Student's own Upcoming
Booking and otherwise shows only currently Bookable Slots. Other Students' Bookings,
Blocked Time, and Slot Holds remove selection opportunities without revealing their
existence or details.

Provider synchronization is deferred from the first scheduling release. A confirmed
Booking instead offers a downloadable `.ics` **Calendar Export** immediately and from
its details modal; rescheduling produces an updated export. This file is a snapshot and
does not make the recipient's calendar authoritative or synchronized.

## Cancellation and rescheduling policy

- At least 24 hours before a Booking, a Student may cancel without losing value and may
  self-service reschedule without a funding penalty. A canceled paid Booking grants one
  Session Credit by default rather than automatically issuing a Stripe refund; an
  ordinary Session Credit or First Session Promotion is restored.
- Inside 24 hours, cancellation remains available only after an explicit warning that
  payment, Session Credit, or promotion will be forfeited. Self-service rescheduling is
  disabled and the Student is directed to contact the Tutor by email.
- The Tutor may use a Tutor Override to reschedule or otherwise edit the Booking without
  penalizing the Student; Tutor-initiated changes preserve funding by default.
- Rescheduling retains the original successful payment, Session Credit redemption, or
  promotion instead of refunding and charging or redeeming again.
- There is no per-Booking reschedule counter. A Student may self-service reschedule
  repeatedly while the Booking remains at least 24 hours away.
- Stripe refunds are never automatic from ordinary Student cancellation. A refund must
  be requested separately so the corresponding replacement Session Credit cannot also
  remain spendable.

An early paid cancellation grants a replacement Session Credit. The Student may create
a **Refund Request**, which freezes that credit while the Tutor reviews it. Approval
issues a full Stripe refund and removes the frozen credit; decline restores the credit
for use. This prevents the same canceled payment from producing both spendable credit
and returned money. Partial refunds are deferred.

## Tutor Dashboard interaction

The desktop Tutor Dashboard places a searchable Student list on the left, the weekly
calendar on the right, and the active Inquiry list below both. Selecting a Booking on
the calendar does not open a modal; it highlights the associated Student and scrolls
that Student into view in the list. The Tutor then selects the Student explicitly to
open the Student Detail modal.

The first release permits at most one **Upcoming Booking** per Student. A Student may
schedule another after the current Booking occurs or is canceled. The Student Detail
modal therefore displays one unambiguous Upcoming Booking for Tutor edits.

The modal's note history contains only Tutor-only Lesson Note Drafts and published
Shared Lesson Notes, with explicit state labels and Publish controls. Private Tutor
Notes do not appear in this list or reuse its CRUD form; a separate private-note area
is deferred.

Student Dashboard welcome guidance is static, code-managed content above the two-panel
layout. It is neither a Lesson Note record nor Tutor-editable content.

The Student information block displays read-only display name and login email plus the
available Session Credit count, First Session Promotion status, and Upcoming Booking
summary. Tutor editing of Student identity is deferred; changing the login email will
require a separate verified identity-change workflow.

The Student Dashboard also exposes the Student's available Session Credit balance,
First Session Promotion status, and pending Refund Request status.

Tutor edits normally select an available Bookable Slot. A Tutor Override may move a
Booking to any otherwise-unoccupied 60-minute time outside normal Availability Windows
after a clear warning; the original payment, Session Credit, or promotion remains
attached.

All self-service Bookings are remote in the first release. Each Booking includes
optional Tutor-controlled **Meeting Details** for the video link or connection
instructions. They are visible only to the associated Student, appear in Booking views,
and are included in the `.ics` Calendar Export. A Booking may be confirmed while those
details are pending, and the Tutor may update them later without changing funding.

Tutor settings provide one default remote Meeting Details value. Each new Booking
copies the current default, and the Tutor may edit the Booking's snapshot without later
default changes rewriting existing Bookings.

Exceptional in-person arrangements remain manual: the Tutor coordinates through email,
updates Meeting Details with the address, and schedules around travel using ordinary
Availability Windows or Blocked Time. The application has no Meeting Mode, Proposed
Location, or automatic travel-buffer logic in the first release.

Meeting-detail and other Booking edits appear immediately in both dashboards and in
future Calendar Exports. The first release sends no automated change notification; the
Tutor communicates changes through the normal personalized email workflow.

Automated Booking reminders are also deferred.
