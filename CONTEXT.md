# Tutoring Platform

This context describes the language of a single-tutor business and distinguishes the
pilot's request flow from the future confirmed booking flow.

## Language

**Tutor**:
The single business owner who manages students, invitations, sessions, and business
records.
_Avoid_: Admin, provider, tutor organization

**Prospect**:
A visitor evaluating the tutor who has no established tutoring relationship.
_Avoid_: Lead, anonymous student

**Inquiry**:
A Prospect's public request to discuss tutoring, containing contact information and an
optional message. It grants no application access and may lead the Tutor to create a
separate Invitation.
_Avoid_: Signup request, account request, Invitation

**New Inquiry**:
An Inquiry awaiting Tutor review that has no linked Invitation.
_Avoid_: Pending signup, Invitee

**Invited Inquiry**:
An Inquiry for which the Tutor has created an Invitation Link. It remains active until
the Invitation is claimed or the Inquiry is archived.
_Avoid_: Student, claimed Inquiry

**Archived Inquiry**:
An Inquiry intentionally removed from the Tutor's active work without creating or
changing account access.
_Avoid_: Deleted account, rejected Student

**Invitee**:
A known prospect with a tutor-created invitation who has not yet claimed a student
account.
_Avoid_: Student, user

**Student**:
A person with a verified account and an established tutoring relationship.
_Avoid_: Invitee, customer, user

**Invitation**:
A revocable, expirable pre-account record bound to one normalized email address and
reached through an opaque token.
_Avoid_: Signup link, student account

**Invitation Link**:
A single-use, expiring link delivered by the Tutor that authorizes its Invitee to set
up and claim the bound Student account.
_Avoid_: Login Link, Magic Link

**Created Invitation**:
An Invitation whose access token has been issued but whose personalized setup page has
not yet been successfully opened.
_Avoid_: Draft Invitation, active Invitation

**Opened Invitation**:
An Invitation whose personalized setup data has been successfully served at least once,
whether requested by its Invitee or an automated link scanner. It remains available
until claimed, expired, or revoked.
_Avoid_: Active Invitation, viewed Invitation

**Invitation Claim**:
The one-time atomic association of an active Invitation with the Student account set
up by the holder of its Invitation Link.
_Avoid_: Signup, payment

**Login Link**:
A short-lived, single-use link requested by an existing account holder to start a new
Student Session or Tutor session.
_Avoid_: Invitation Link, password-reset link

**Private Tutor Note**:
Tutor-authored context that is never visible through invitee or student boundaries.
_Avoid_: Personal message, shared note

**Shared Personal Message**:
Tutor-authored invitation context intentionally visible to its invitee.
_Avoid_: Private note

**Shared Lesson Note**:
Lesson context deliberately shared with its Student for exactly one past Booking. Its
displayed session date is the Booking's fixed tutoring date.
_Avoid_: Private tutor note, visibility toggle

**Lesson Note Draft**:
Tutor-authored lesson context intended for later publication but visible only to the
Tutor until explicitly published.
_Avoid_: Shared Lesson Note, Private Tutor Note

**Session Request**:
A student's pending proposal for a tutoring service and preferred time; it is neither
confirmed nor paid.
_Avoid_: Booking, session

**Booking**:
A confirmed tutoring session with an authoritative time and payment relationship.
_Avoid_: Session request

**Upcoming Booking**:
The single confirmed Booking for a Student whose tutoring start is still in the future.
The first release permits at most one per Student.
_Avoid_: Next session, Session Request

**Meeting Details**:
Tutor-controlled Student-visible information explaining where or how a Booking occurs,
such as an address or remote-session instructions.
_Avoid_: Private Tutor Note, Availability Window

**Session Credit**:
A non-currency entitlement on a Student's account that may be redeemed for one
60-minute Booking.
_Avoid_: Refund, coupon, payment balance

**First Session Promotion**:
A one-time entitlement automatically funding a Student's earliest eligible Booking,
recorded separately from ordinary Session Credits.
_Avoid_: Session Credit, coupon code, permanent discount

**Session Price**:
The Tutor-configured global USD amount charged for a future directly paid 60-minute
Booking. Each payment snapshots the applicable amount.
_Avoid_: Session Credit, payment balance, historical payment amount

**Tutor Timezone**:
The single Tutor-configured IANA timezone used to define and display all Availability
Windows, Bookable Slots, and Bookings in the local-client release.
_Avoid_: Student timezone, browser timezone

**Tutor Override**:
An explicit Tutor-authorized exception to normal Booking policy. Tutor-initiated
changes preserve the Student's funding by default.
_Avoid_: Student reschedule, automatic penalty

**Refund Request**:
A Student's request to replace the frozen Session Credit from an early paid cancellation
with a full Stripe refund, subject to Tutor approval.
_Avoid_: Automatic refund, cancellation, Session Credit

**Availability Window**:
A Tutor-defined period during which a Booking may be scheduled if its full duration
remains free. Empty calendar time outside an Availability Window is not bookable.
_Avoid_: Empty time, Booking, open calendar

**Bookable Slot**:
A derived 60-minute interval a Student may select inside an Availability Window. Slots
begin at the window's start and repeat in one-hour increments while fully free.
_Avoid_: Programmable spot, empty calendar space, Booking

**Slot Hold**:
A temporary reservation preventing competing selection of a Bookable Slot while one
Student completes paid checkout. It becomes a Booking on payment or expires unused.
_Avoid_: Booking, Session Request, Availability Window

**Blocked Time**:
A date-specific Tutor override that removes overlapping Bookable Slots without changing
the recurring Availability Windows.
_Avoid_: Booking, cancellation, deleted availability

**Student Session**:
A revocable server-side authentication record referenced by an opaque secure cookie.
_Avoid_: Booking, tutoring session

**Calendar Projection**:
An external calendar event that mirrors a booking without becoming its source of truth.
_Avoid_: Booking

**Calendar Export**:
A downloadable `.ics` snapshot of a Booking that creates no ongoing synchronization
relationship with the recipient's calendar.
_Avoid_: Calendar Projection, Booking, calendar sync

**Sync Drift**:
A detected mismatch between a booking and its calendar projection that requires
reconciliation.
_Avoid_: Reschedule, cancellation
