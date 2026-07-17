# 05 — Tutor business settings

**What to build:** Give the Tutor one authoritative place to configure the price, timezone, and default remote connection information used by future Bookings.

**Blocked by:** None — can start immediately.

**Status:** resolved

- [x] The Tutor can view and update one global USD Session Price represented and persisted as integer cents.
- [x] The Tutor can configure one valid IANA Tutor Timezone used by all first-release calendar displays and scheduling rules.
- [x] The Tutor can configure default remote Meeting Details that may be empty or pending.
- [x] Only the Tutor can read or mutate business settings, and every unsafe mutation requires the established same-origin and CSRF protections.
- [x] Invalid currency, amount, timezone, or secret configuration fails safely and does not partially update settings.
- [x] Setting changes affect only future payment and Meeting Details snapshots; historical Booking values never change retroactively.
- [x] Black-box HTTP tests cover validation, authorization, CSRF/origin enforcement, integer precision, and snapshot boundaries.

## Answer

The singleton Tutor settings remain integer-cent USD values with IANA timezone and
optional Meeting Details validation. Booking creation now copies price, currency, and
Meeting Details into immutable Booking fields in the same transaction; changing the
settings leaves the existing Booking unchanged and affects the next Booking only.
Tutor authorization, origin, CSRF, validation, precision, and the real snapshot boundary
are covered through black-box HTTP tests.
