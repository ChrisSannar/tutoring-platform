# Boundaries

- One application and database own identity, Invitations, availability, Session
  Credits, Bookings, Login Requests, and lesson notes.
- Invitation and Login Links are manually delivered; the application sends no email.
- Login Link inspection is scanner-safe and confirmation is an explicit POST.
- Session Credits are non-currency entitlements recorded in an immutable Credit Ledger.
- Bookings are either `session_credit` or `complimentary`.
- Calendar Export is a static `.ics` snapshot.
- There is no purchasing, payment tracking, notification delivery, or calendar sync.
- Pilot data is disposable and the squashed initial migration is authoritative.
