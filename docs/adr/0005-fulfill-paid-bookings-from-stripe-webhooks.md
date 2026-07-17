# Fulfill paid Bookings from verified Stripe webhooks

The application remains authoritative for Bookable Slots and paid Bookings. Starting
Stripe Checkout atomically snapshots the server-owned USD price and creates a 30-minute
Slot Hold. The hold removes the interval from every Student's choices while payment is
pending and expires through deterministic lazy reconciliation; no scheduler is required.

A browser return is advisory status only. It never proves payment and never creates a
Booking. Only a correctly signed Stripe webhook whose Checkout Session, Student, slot,
currency, and integer amount match the stored expectation may atomically convert the
hold into one paid Booking and immutable payment evidence. Provider event IDs, Checkout
Session IDs, idempotency keys, and the normal Booking conflict checks prevent duplicate
fulfillment under retries or concurrency.

Development and tests use the same adapter boundary with a deterministic local fake and
signed fixtures, so the critical suite never requires external network access. Production
fails closed unless its Stripe secret and webhook-signing secret are configured.
