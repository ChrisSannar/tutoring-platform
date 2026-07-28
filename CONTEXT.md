# Tutoring Platform

This context describes one Tutor's business centered on Inquiries, Invitations,
Session Credits, direct Bookings, and shared lesson material.

## Language

**Tutor**:
The single business owner who manages Students, Invitations, availability, Bookings,
Session Credits, and lesson records.
_Avoid_: Admin, provider, tutor organization

**Prospect**:
A visitor evaluating the Tutor who has no established tutoring relationship.
_Avoid_: Student, Invitee

**Inquiry**:
A Prospect's public request to discuss tutoring. It grants no application access.
_Avoid_: Signup request, Invitation

**Invitee**:
A known Prospect with a Tutor-created Invitation who has not claimed a Student account.
_Avoid_: Student, user

**Invitation**:
A revocable, expirable pre-account record bound to one normalized email address.
_Avoid_: Login Link, Student account

**Invitation Link**:
A single-use link delivered manually by the Tutor that lets the bound Invitee claim a
Student account.
_Avoid_: Login Link, Magic Link

**Invitation Claim**:
The atomic association of an active Invitation with a new Student account. It grants
one Session Credit.
_Avoid_: Signup

**Student**:
A person with a verified account and an established tutoring relationship.
_Avoid_: Invitee, customer, user

**Login Request**:
A returning account holder's public request awaiting manual Tutor generation and
delivery of a Login Link.
_Avoid_: Inquiry, Invitation

**Login Link**:
A short-lived, single-use link that starts a Student Session or Tutor session. Opening
the link never authenticates; the holder must use its confirmation action.
_Avoid_: Invitation Link, password reset

**Student Session**:
A revocable server-side authentication record referenced by an opaque secure cookie.
_Avoid_: Booking, tutoring session

**Availability Window**:
A Tutor-defined period during which a Booking may be scheduled.
_Avoid_: Empty time, Booking

**Blocked Time**:
A date-specific Tutor override that removes overlapping Bookable Slots.
_Avoid_: Booking, deleted availability

**Bookable Slot**:
A derived 60-minute interval inside an Availability Window that is free and at least
24 hours away.
_Avoid_: Empty calendar space, Booking

**Booking**:
A confirmed 60-minute tutoring session with an authoritative time and funding kind.
_Avoid_: Session Request

**Upcoming Booking**:
The single confirmed Booking for a Student whose end time has not passed. A Student may
have at most one.
_Avoid_: Session Request

**Past Booking**:
A non-cancelled Booking whose end time has passed. Reconciliation records this state and
replenishes a redeemed Session Credit exactly once.
_Avoid_: Completed status, cancelled Booking

**Complimentary Booking**:
A Tutor-created Booking that neither consumes nor replenishes a Session Credit.
_Avoid_: Session Credit-funded Booking

**Session Credit**:
A non-currency entitlement redeemed for one Booking. Invitation Claim grants one;
Student-funded cancellation or a Past Booking replenishes it exactly once. Tutor
adjustments may create any non-negative balance.
_Avoid_: Refund, coupon, editable balance

**Credit Ledger**:
The immutable history of Session Credit grants, redemptions, replenishments, and Tutor
adjustments.
_Avoid_: Editable balance

**Tutor Timezone**:
The Tutor-configured IANA timezone used for Availability Windows, Bookable Slots, and
Bookings.
_Avoid_: Browser timezone

**Tutor Override**:
An explicit Tutor-authorized exception to normal Booking availability.
_Avoid_: Student reschedule

**Booking Focus**:
An optional short Student-authored description of what to work on.
_Avoid_: Lesson Note

**Meeting Details**:
Tutor-controlled Student-visible connection instructions snapshotted on a Booking.
_Avoid_: Private Tutor Note

**Lesson Note Draft**:
Tutor-authored lesson context visible only to the Tutor until publication.

**Shared Lesson Note**:
Published lesson context visible to the Student for one Past Booking.

**Calendar Export**:
A downloadable `.ics` snapshot of an Upcoming Booking.
_Avoid_: Calendar sync
