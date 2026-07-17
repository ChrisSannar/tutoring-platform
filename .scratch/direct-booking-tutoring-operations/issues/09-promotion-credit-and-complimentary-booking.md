# 09 — Promotion, credit, and complimentary Booking

**What to build:** Establish direct Booking without payment-provider complexity by supporting automatic promotion funding, Session Credit redemption, and explicit Tutor-created complimentary sessions.

**Blocked by:** 07 — Availability and Bookable Slots; 08 — Credit Ledger and Tutor adjustments.

**Status:** resolved

- [x] A Student can select one Bookable Slot and then activate a separate **Schedule session** confirmation action.
- [x] Confirmation shows the exact start, 60-minute duration, Tutor Timezone, applicable funding source, and 24-hour policy warning.
- [x] The Student may provide an optional plain-text Booking Focus no longer than 500 characters.
- [x] The earliest eligible Student Booking automatically consumes the First Session Promotion; the Student cannot pay or spend credit to preserve it.
- [x] After the promotion is unavailable, a Student with an available Session Credit can redeem exactly one credit atomically.
- [x] Promotion- and credit-funded Booking creation atomically rechecks slot availability, funding availability, idempotency, and the one-Upcoming-Booking invariant.
- [x] The Tutor can create an explicitly Complimentary Booking without consuming promotion, credit, or payment value.
- [x] A Booking snapshots its funding kind and current default Meeting Details, while allowing those details to remain pending.
- [x] Students see their complete Booking and funding state; other Students see only the absence of the occupied slot.
- [x] Concurrent and retry tests prove that one slot, one funding source, and one Upcoming Booking cannot be duplicated.

## Answer

Students now select a derived slot, review a separate confirmation with the exact policy
and funding facts, and schedule atomically. The transaction consumes the available First
Session Promotion before ordinary credit, rechecks the slot, funding, idempotency key,
and one-Upcoming invariant, and snapshots the current business values. Tutor-created
Complimentary Bookings bypass funding but not availability/conflict rules. Concurrent
and retry tests prove single consumption, while Playwright covers the complete promoted
Booking journey.
