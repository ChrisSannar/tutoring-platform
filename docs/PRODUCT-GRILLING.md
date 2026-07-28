# Product Decisions

The product is a single-Tutor operational tool for Inquiry intake, secure account
access, availability, direct Booking, Session Credits, and lesson notes.

## Locked MVP

- Invitation Claim grants one Session Credit.
- Student-created Booking consumes one credit and each Student has at most one Upcoming
  Booking.
- A Past Booking replenishes its redeemed credit exactly once.
- Student cancellation restores redeemed credit; rescheduling retains funding and keeps
  the 24-hour cutoff.
- The Tutor may adjust credits without an artificial maximum.
- The Tutor controls Upcoming Bookings and may create Complimentary Bookings.
- Past Bookings and their lesson notes remain historical records.
- Invitation and Login Links are manually delivered.
- The Next Booking card is the Tutor's notification.

## Explicitly out

Purchasing, financial records, automated email, reminders, push notifications, calendar
synchronization, and a replacement for Session Credits are outside this MVP.
