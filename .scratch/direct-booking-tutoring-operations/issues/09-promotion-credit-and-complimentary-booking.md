# 09 — Promotion, credit, and complimentary Booking

**What to build:** Establish direct Booking without payment-provider complexity by supporting automatic promotion funding, Session Credit redemption, and explicit Tutor-created complimentary sessions.

**Blocked by:** 07 — Availability and Bookable Slots; 08 — Credit Ledger and Tutor adjustments.

**Status:** ready-for-agent

- [ ] A Student can select one Bookable Slot and then activate a separate **Schedule session** confirmation action.
- [ ] Confirmation shows the exact start, 60-minute duration, Tutor Timezone, applicable funding source, and 24-hour policy warning.
- [ ] The Student may provide an optional plain-text Booking Focus no longer than 500 characters.
- [ ] The earliest eligible Student Booking automatically consumes the First Session Promotion; the Student cannot pay or spend credit to preserve it.
- [ ] After the promotion is unavailable, a Student with an available Session Credit can redeem exactly one credit atomically.
- [ ] Promotion- and credit-funded Booking creation atomically rechecks slot availability, funding availability, idempotency, and the one-Upcoming-Booking invariant.
- [ ] The Tutor can create an explicitly Complimentary Booking without consuming promotion, credit, or payment value.
- [ ] A Booking snapshots its funding kind and current default Meeting Details, while allowing those details to remain pending.
- [ ] Students see their complete Booking and funding state; other Students see only the absence of the occupied slot.
- [ ] Concurrent and retry tests prove that one slot, one funding source, and one Upcoming Booking cannot be duplicated.

