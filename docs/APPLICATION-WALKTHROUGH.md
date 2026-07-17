# Application walkthrough

The cohesive workflow is:

`Landing Inquiry -> Tutor Invitation -> Student claim -> direct Booking -> Tutor lesson operation -> published Shared Lesson Note`

## Application shell and security

`frontend/src/app/Application.tsx` selects the landing, role-neutral sign-in, Tutor,
Invitation, Student, and Checkout-return surfaces without a routing dependency.
`backend/app/main.py` composes the FastAPI routers. Browser calls stay same-origin through
the Vite `/api` proxy; the backend enables no CORS.

Opaque server-side sessions, hashed tokens, exact-origin checks, and CSRF validation live
under `backend/app/authentication/` and `backend/app/http/`. Public errors are sanitized
and include request IDs. `/api/health` is liveness; `/api/ready` verifies database access
and the exact Alembic head.

## Inquiry, Invitation, and access

The landing Inquiry modal creates a bounded public Inquiry without an account. The Tutor
queue creates either an Inquiry-linked or manual seven-day Invitation in one action.
Lookup uses a token hash; encrypted material permits authenticated redisplay until claim,
regeneration, revocation, or expiration erases it.

Opening `/invite/:token` performs an observational GET. **Create Account** is the first
claim mutation and atomically creates the Student account, authenticated Student Session,
and First Session Promotion. Returning accounts use the role-neutral Login Request flow;
the Tutor manually generates a 15-minute Login Link.

## Direct Booking

The Tutor owns the USD price, timezone, Meeting Details default, recurring Availability
Windows, Blocked Time, and explicit Overrides. `backend/app/availability/` derives
privacy-safe 60-minute Bookable Slots between 24 hours and eight weeks ahead.

`backend/app/bookings/` creates one Upcoming Booking transactionally. Funding consumes the
First Session Promotion first, then one Session Credit. Students without either begin a
server-priced Stripe Checkout. `backend/app/checkout/` creates a 30-minute Slot Hold and
only an exact timestamp-signed successful webhook creates one paid Booking and immutable
payment evidence. `/checkout/return` is status-only.

Students may reschedule outside 24 hours and cancel under the explicit restoration or
forfeiture policy. Early paid cancellation creates one replacement Session Credit. A
Refund Request freezes that credit; Tutor decline restores it once, while idempotent full
provider success records refund evidence and leaves no spendable replacement value.

## Tutor and Student workspaces

On desktop the Student workspace places Shared Lesson Notes left and the calendar right;
on smaller screens the calendar precedes notes. The Tutor workspace places Student search
left and the weekly Booking calendar right, with Login Request and Inquiry queues below.
There is no second scheduling model or service selector.

A non-canceled Booking becomes note-eligible when its 60-minute end passes. The Tutor
saves a private Lesson Note Draft and explicitly publishes it. Students receive only
published notes in the canonical accordion and may download the original Markdown.

## Persistence and verification

Alembic is the only schema authority; application startup never migrates. Migration
`20260717_0017` drops the superseded historical Session Request table without converting
rows to Bookings.

`bun run test` runs black-box backend behavior and Playwright. The browser harness creates
a fresh migrated database, bootstraps the Tutor, selects randomized localhost ports, owns
both processes, and tears everything down. A Tutor-authenticated, test-environment-only
clock endpoint lets the critical journey derive a Past Booking without sleeps; production
returns no such capability.
