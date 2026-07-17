# 11 — Student Booking changes and Calendar Export

**What to build:** Let a Student responsibly reschedule or cancel their Booking under the 24-hour policy and keep a portable calendar snapshot of the authoritative Booking.

**Blocked by:** 09 — Promotion, credit, and complimentary Booking.

**Status:** resolved

- [x] At least 24 hours before start, a Student can reschedule repeatedly to a free Bookable Slot while preserving the original funding.
- [x] At least 24 hours before start, cancellation restores redeemed Session Credit or First Session Promotion as applicable.
- [x] Early cancellation of a paid Booking is represented so that one replacement Session Credit can be granted when paid funding becomes available.
- [x] Inside 24 hours, self-service rescheduling is disabled and the interface directs the Student to contact the Tutor by normal email.
- [x] Inside 24 hours, cancellation requires explicit confirmation that the original promotion, credit, or paid value will be forfeited.
- [x] Boundary behavior is consistent immediately before, exactly at, and inside 24 hours.
- [x] A confirmed Booking exposes a downloadable `.ics` Calendar Export with stable UID, 60-minute duration, Tutor Timezone, current Meeting Details, and safe filename.
- [x] A rescheduled Booking produces an updated export for the new authoritative details without claiming ongoing synchronization.
- [x] Black-box tests cover ownership, conflict checks, funding restoration/forfeiture, retries, controlled-clock boundaries, export escaping, and authorization.

## Answer

Students can repeatedly move an early Booking to a current Bookable Slot without
changing its funding. Early cancellation appends the corresponding promotion, credit,
or future paid-replacement restoration event; inside 24 hours rescheduling is replaced
by normal-email guidance and cancellation requires explicit forfeiture confirmation.
The exact 24-hour boundary remains early. Change receipts make retries idempotent and
ownership/conflicts are rechecked. Each Upcoming Booking exposes a safe `.ics` snapshot
with stable UID, Tutor Timezone, escaped current details, and an updated start after
rescheduling.
