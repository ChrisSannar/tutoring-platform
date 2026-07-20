# 01 — Document deferred Stripe hardening

**What to build:** Document the current payment boundary so the Tutor can operate safely with external payment methods while Stripe hardening remains intentionally deferred.

**Blocked by:** None — can start immediately.

**Status:** resolved

- [x] Product and operational documentation identifies Stripe Checkout and Refund Request fulfillment as non-critical, deferred functionality rather than a dependable production payment path.
- [x] The documented Stripe risks include missing provider idempotency and reconciliation during Checkout creation, non-monotonic Checkout expiration, provider network calls held inside database write transactions, insufficient real-concurrency proof, and duplicated payment occupancy logic.
- [x] The fallback permits the Tutor to arrange Venmo, cash, or another external payment method without implying that the application verifies or records that payment.
- [x] Documentation states that an externally paid Booking must not be represented as Complimentary or Session Credit funded merely to bypass the missing payment workflow.
- [x] The future hardening boundary remains consistent with verified-webhook fulfillment and preserves the application as the authority for Booking state.

## Answer

`docs/PRODUCT-GRILLING.md` now records the product decision: Stripe Checkout and Refund
Request fulfillment are deferred, external payment may be arranged outside the application,
and external payment must not be disguised as Complimentary or Session Credit funding.

`docs/HANDOFF.md` is the single operational risk inventory. It lists the five known
hardening gaps, states that the application neither verifies nor records Venmo, cash, or
other external payment, and preserves ADR 0005's verified-webhook and application-authority
boundary for future work.

Verification: checked both documents for every acceptance phrase, checked their relative
Markdown links resolve, and ran `git diff --check`.
