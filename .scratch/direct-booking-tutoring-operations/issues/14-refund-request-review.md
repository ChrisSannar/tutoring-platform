# 14 — Refund Request review

**What to build:** Let a Student ask to exchange the replacement credit from an early paid cancellation for a full refund, with Tutor review and exactly-one-form-of-value enforcement.

**Blocked by:** 08 — Credit Ledger and Tutor adjustments; 11 — Student Booking changes and Calendar Export; 13 — Stripe Checkout and Slot Holds.

**Status:** resolved

- [x] Early cancellation of a paid Booking grants exactly one replacement Session Credit tied to the original payment evidence.
- [x] The eligible Student can create one Refund Request for that canceled Booking.
- [x] Creating the request freezes the exact replacement credit so it cannot fund a Booking while review is pending.
- [x] Student and Tutor dashboards show the minimum appropriate pending Refund Request state.
- [x] The Tutor can decline the request, restoring the frozen credit exactly once.
- [x] The Tutor can approve only a full refund; verified provider success removes the frozen credit and records the completed refund outcome.
- [x] Provider failure leaves the request and frozen value in a safely retryable state rather than losing or duplicating value.
- [x] Retries and concurrent review actions cannot give the Student both refunded money and spendable credit.
- [x] Black-box tests cover eligibility, ownership, freeze/unfreeze, approval, decline, provider failure, idempotency, concurrency, and cross-role denial.

## Answer

An owned canceled paid Booking with its original payment evidence and replacement-credit
ledger event can produce exactly one Refund Request. Creation freezes one credit in the
same transaction. Students see their bounded status list, while the Tutor receives a
minimal pending queue with only full approval or decline. Decline unfreezes the credit
once. Approval sends the immutable original payment identifier and full snapshotted
amount through an idempotent provider adapter, then records unique refund evidence;
provider failure rolls back and leaves the request pending. Transactional review and
terminal-state retries prevent refunded money and spendable replacement credit from
coexisting.
