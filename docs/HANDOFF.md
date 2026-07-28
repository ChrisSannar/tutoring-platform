# Handoff

The live model is Credit-Only Booking. Direct Booking remains the sole scheduling
model; Session Request and all purchasing flows are retired.

The authoritative domain language is in `CONTEXT.md`. The initial squashed migration
contains no purchasing tables or fields. Invitation Claim grants one Session Credit,
Student Booking redeems it, and lazy reconciliation restores it once when the Booking
becomes Past. Tutor adjustments may raise balances above one.

Student cancellation always restores redeemed credit. Student rescheduling retains
funding and keeps the 24-hour cutoff. The Tutor has full control over Upcoming Bookings
and may create Complimentary Bookings, which never change credits. Past Bookings and
lesson notes remain historical records.

Run the full repository gate with:

```bash
bun run test
```

The critical Playwright journey is `e2e/critical-journey.spec.ts`.
