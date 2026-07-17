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
