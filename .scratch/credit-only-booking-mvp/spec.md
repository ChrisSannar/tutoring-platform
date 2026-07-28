# Credit-Only Booking MVP

Status: implemented

## Outcome

The application supports Inquiry, Invitation Link, Login Link, availability, direct
Booking, lesson-note, and `.ics` flows without purchasing or financial records.

## Model

- Invitation Claim atomically grants one Session Credit.
- Student Booking requires and redeems one credit.
- A non-cancelled Student-funded Booking becomes Past after its 60-minute end and
  replenishes one credit exactly once.
- Reconciliation runs before funding, Booking, and Tutor-dashboard operations.
- Each Student may have one Upcoming Booking.
- Tutor credit adjustments may raise the balance above one.
- Tutor-created Complimentary Bookings never consume or replenish credits.
- Student or Tutor cancellation restores Student funding exactly once.
- Student rescheduling retains funding and keeps the 24-hour cutoff.
- Past Bookings and lesson notes are read-only history.

## Interfaces

Funding responses contain only `{ session_credits }`. Booking responses contain no
purchasing fields. Tutor settings contain timezone and default Meeting Details.

Purchasing, webhook, and refund routes and schema objects do not exist. Invitation,
Login Request, Login Link confirmation, Booking, rescheduling, availability,
lesson-note, and Calendar Export routes remain.

The landing page offers an “I’m already a student” Login Request modal. Authenticated
Students visiting `/` go directly to `/student`. Invitation Claim confirms the bound
email and instructs an Invitee with the wrong email to contact the Tutor.

## Verification

Black-box tests cover atomic credit grant, redemption, one-Upcoming enforcement,
idempotent concurrent replenishment, cancellation, Tutor CRUD boundaries, rescheduling,
route/schema absence, and `.ics`. Playwright owns the critical browser journey. The
repository gate is `bun run test`.
