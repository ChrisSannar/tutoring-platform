# Current Handoff — 2026-07-17

## Current state

The direct-Booking product slice is complete. Public Inquiry intake leads to an
Inquiry-linked Invitation, one-step Student claim, promotion/credit/paid Booking,
Booking changes, refunds, and published Shared Lesson Notes. Direct Booking is the sole
scheduling model.

The former Session Request pilot was discarded by migration `20260717_0017`. Historical
rows are dropped without creating Bookings; its old routes, models, tests, service
selector, and Student/Tutor UI are removed.

## Verification

Run from repository root:

```bash
bun run test
```

The backend suite includes authorization, CSRF/origin, ownership, idempotency,
concurrency, funding, Stripe signature, refund, and retirement behavior. Playwright owns
isolated migrated state and both randomized-port processes. Its critical journey proves
Inquiry through published Lesson Note without external services.

## Operational notes

- Production requires an explicit database URL, Invitation encryption key, Stripe mode,
  Stripe secret key, and Stripe webhook secret.
- Development payment uses deterministic provider fakes; browser returns never prove
  payment.
- Use `bun run migrate:dev` before serving an existing development database.
- Use separate Tutor and Student browser profiles because role sign-in rotates the same
  session-cookie name.

### Deferred payment operation

Stripe Checkout and Refund Request fulfillment are non-critical and intentionally
deferred; do not depend on either as a production payment path. Known hardening gaps are:

- Checkout creation has no provider idempotency key or reconciliation after an ambiguous
  provider response.
- Checkout expiration is not monotonic, so stale work can overwrite a later terminal
  state.
- Provider network calls occur while database write transactions remain open.
- Tests do not yet prove payment behavior under real concurrent requests.
- Payment duplicates Booking occupancy rules instead of routing through the shared
  occupancy policy.

The Tutor may arrange Venmo, cash, or another external payment outside the application;
the application neither verifies nor records that payment. Do not label an externally
paid appointment as a Complimentary Booking or Session Credit-funded Booking to get it
through the current workflow.

When payment hardening resumes, preserve
[ADR 0005](adr/0005-fulfill-paid-bookings-from-stripe-webhooks.md): the application owns
Bookable Slot and Booking state, browser returns remain advisory, and only a verified
Stripe webhook fulfills a paid Booking.
