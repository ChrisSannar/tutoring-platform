# 14 — Refund Request review

**What to build:** Let a Student ask to exchange the replacement credit from an early paid cancellation for a full refund, with Tutor review and exactly-one-form-of-value enforcement.

**Blocked by:** 08 — Credit Ledger and Tutor adjustments; 11 — Student Booking changes and Calendar Export; 13 — Stripe Checkout and Slot Holds.

**Status:** ready-for-agent

- [ ] Early cancellation of a paid Booking grants exactly one replacement Session Credit tied to the original payment evidence.
- [ ] The eligible Student can create one Refund Request for that canceled Booking.
- [ ] Creating the request freezes the exact replacement credit so it cannot fund a Booking while review is pending.
- [ ] Student and Tutor dashboards show the minimum appropriate pending Refund Request state.
- [ ] The Tutor can decline the request, restoring the frozen credit exactly once.
- [ ] The Tutor can approve only a full refund; verified provider success removes the frozen credit and records the completed refund outcome.
- [ ] Provider failure leaves the request and frozen value in a safely retryable state rather than losing or duplicating value.
- [ ] Retries and concurrent review actions cannot give the Student both refunded money and spendable credit.
- [ ] Black-box tests cover eligibility, ownership, freeze/unfreeze, approval, decline, provider failure, idempotency, concurrency, and cross-role denial.

