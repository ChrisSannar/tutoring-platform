# Application Walkthrough

The FastAPI backend and React frontend share one browser origin. The backend owns
authentication, Invitation lifecycle, availability, the Credit Ledger, Booking state,
and lesson notes.

## Public and access flow

A Prospect may submit an Inquiry or use “I’m already a student” to create a Login
Request. The Tutor manually creates Invitation Links and Login Links. Invitation setup
shows the bound email and collects only the display name. Login Links require an
explicit confirmation action.

Invitation Claim atomically creates the Student account and grants one Session Credit.
An authenticated Student visiting `/` is redirected to `/student`; Tutor landing
behavior is unchanged.

## Booking flow

The Tutor defines Availability Windows, Blocked Time, Tutor Overrides, timezone, and
default Meeting Details. The application derives 60-minute Bookable Slots.

A Student may hold one Upcoming Booking and needs one Session Credit to create it.
Creation redeems the credit atomically. Reconciliation runs before funding, Booking,
and Tutor-dashboard operations: once the Booking end passes it becomes Past and its
credit is replenished exactly once. Cancellation also restores Student funding exactly
once. Student rescheduling retains funding and is unavailable inside 24 hours.

The Tutor may create Complimentary Bookings, edit or move Upcoming Bookings, and cancel
them. Complimentary Bookings never alter credits. Past Bookings are read-only history
and remain eligible for Lesson Note Drafts and publication.

Calendar Export is a static `.ics` download. No calendar synchronization or notification
subsystem exists.
