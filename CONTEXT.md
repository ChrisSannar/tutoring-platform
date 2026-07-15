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

**Invitation Claim**:
The one-time atomic association of an active invitation with the student account that
verified its bound email address.
_Avoid_: Signup, payment

**Private Tutor Note**:
Tutor-authored context that is never visible through invitee or student boundaries.
_Avoid_: Personal message, shared note

**Shared Personal Message**:
Tutor-authored invitation context intentionally visible to its invitee.
_Avoid_: Private note

**Shared Lesson Note**:
Lesson context deliberately shared with its student as a record distinct from private
tutor notes.
_Avoid_: Private tutor note, visibility toggle

**Session Request**:
A student's pending proposal for a tutoring service and preferred time; it is neither
confirmed nor paid.
_Avoid_: Booking, session

**Booking**:
A confirmed tutoring session with an authoritative time and payment relationship.
_Avoid_: Session request

**Student Session**:
A revocable server-side authentication record referenced by an opaque secure cookie.
_Avoid_: Booking, tutoring session

**Calendar Projection**:
An external calendar event that mirrors a booking without becoming its source of truth.
_Avoid_: Booking

**Sync Drift**:
A detected mismatch between a booking and its calendar projection that requires
reconciliation.
_Avoid_: Reschedule, cancellation
