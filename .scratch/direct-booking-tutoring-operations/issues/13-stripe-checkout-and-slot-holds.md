# 13 — Stripe Checkout and Slot Holds

**What to build:** Add exact-price Stripe-hosted payment as another Booking funding adapter while keeping the platform authoritative for slots and verified webhook fulfillment.

**Blocked by:** 05 — Tutor business settings; 07 — Availability and Bookable Slots; 09 — Promotion, credit, and complimentary Booking.

**Status:** claimed

- [x] A short ADR records that verified Stripe webhook fulfillment, not browser redirect, creates a paid Booking and that a 30-minute Slot Hold protects checkout availability.
- [ ] A Student without promotion or credit can begin Stripe-hosted Checkout for a selected Bookable Slot.
- [ ] The server reads the exact USD Session Price from Tutor settings, snapshots integer cents, and never accepts a browser-supplied amount.
- [ ] Starting Checkout atomically creates a 30-minute Slot Hold that removes the slot from every Student's available choices.
- [ ] Failed, abandoned, or expired Checkout releases the hold through deterministic lazy cleanup or explicit reconciliation without a required scheduler.
- [ ] Only a correctly signed, successful webhook matching the expected Student, slot, currency, and amount converts the hold into one paid Booking.
- [ ] Duplicate or concurrent provider events and Checkout Session identifiers cannot create duplicate Bookings or payment evidence.
- [ ] Browser return improves status visibility but never independently proves payment or creates a Booking.
- [ ] Payment configuration fails closed outside development, and logs exclude secrets, payment details, personal content, and token material.
- [ ] Deterministic provider fakes and signed fixtures cover success, delay, mismatch, expiry, invalid signatures, retry, concurrency, and reconciliation without external network access.
