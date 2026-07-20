# 05 — Centralize and prove non-payment Booking occupancy

**What to build:** Make non-payment Booking operations rely on one authoritative occupancy policy and prove that simultaneous attempts cannot consume the same slot or funding twice.

**Blocked by:** None — can start immediately.

**Status:** resolved

- [x] Availability, promotion- and Session Credit-funded Booking creation, Tutor Booking operations, and Student rescheduling share one transaction-aware definition of overlapping Bookings, Blocked Time, and active Slot Holds.
- [x] UTC-aware datetime normalization is centralized for the non-payment scheduling paths instead of being independently reimplemented.
- [x] Policy-specific exclusions, such as ignoring the Booking currently being rescheduled, remain explicit at the shared boundary.
- [x] A live-server or equivalent genuinely overlapping concurrency test proves that two Students cannot claim one slot and that one Student cannot consume promotion or Session Credit funding twice.
- [x] The test demonstrates actual request overlap rather than relying on event-loop scheduling of synchronous handlers.
- [x] Stripe Checkout and Refund Request restructuring remains outside this ticket and is referenced as deferred payment hardening.

## Answer

Non-payment scheduling now reads Booking, Blocked Time, and active Slot Hold
occupancy through `app.occupancy` on the caller's transaction connection. Bookable
Slot derivation accepts that same connection, while Student and Tutor rescheduling
pass an explicit Booking exclusion. Incoming non-payment Booking instants and stored
occupancy are normalized through the same UTC-aware helper.

The Booking HTTP test starts a live Uvicorn server with two worker processes and
releases two independent HTTP requests through a thread barrier. It also asserts the
requests were simultaneously in flight. The test records one `201` and one `409` for
two Students racing for one slot, one Student racing to consume one promotion twice,
and one Student racing to consume one Session Credit twice. Public funding responses
confirm only one funding consumption in each funding race.

Verification: the self-excluding, UTC-normalizing Student reschedule tracer passed;
the live concurrency test passed; the authoritative backend suite passed 100 tests.

Stripe Checkout and Refund Request restructuring remains deferred to issue 01 and
the verified-webhook boundary in `docs/adr/0005-fulfill-paid-bookings-from-stripe-webhooks.md`.
