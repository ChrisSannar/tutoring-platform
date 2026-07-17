# 11 — Student Booking changes and Calendar Export

**What to build:** Let a Student responsibly reschedule or cancel their Booking under the 24-hour policy and keep a portable calendar snapshot of the authoritative Booking.

**Blocked by:** 09 — Promotion, credit, and complimentary Booking.

**Status:** ready-for-agent

- [ ] At least 24 hours before start, a Student can reschedule repeatedly to a free Bookable Slot while preserving the original funding.
- [ ] At least 24 hours before start, cancellation restores redeemed Session Credit or First Session Promotion as applicable.
- [ ] Early cancellation of a paid Booking is represented so that one replacement Session Credit can be granted when paid funding becomes available.
- [ ] Inside 24 hours, self-service rescheduling is disabled and the interface directs the Student to contact the Tutor by normal email.
- [ ] Inside 24 hours, cancellation requires explicit confirmation that the original promotion, credit, or paid value will be forfeited.
- [ ] Boundary behavior is consistent immediately before, exactly at, and inside 24 hours.
- [ ] A confirmed Booking exposes a downloadable `.ics` Calendar Export with stable UID, 60-minute duration, Tutor Timezone, current Meeting Details, and safe filename.
- [ ] A rescheduled Booking produces an updated export for the new authoritative details without claiming ongoing synchronization.
- [ ] Black-box tests cover ownership, conflict checks, funding restoration/forfeiture, retries, controlled-clock boundaries, export escaping, and authorization.

