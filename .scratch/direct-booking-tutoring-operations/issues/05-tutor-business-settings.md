# 05 — Tutor business settings

**What to build:** Give the Tutor one authoritative place to configure the price, timezone, and default remote connection information used by future Bookings.

**Blocked by:** None — can start immediately.

**Status:** ready-for-agent

- [ ] The Tutor can view and update one global USD Session Price represented and persisted as integer cents.
- [ ] The Tutor can configure one valid IANA Tutor Timezone used by all first-release calendar displays and scheduling rules.
- [ ] The Tutor can configure default remote Meeting Details that may be empty or pending.
- [ ] Only the Tutor can read or mutate business settings, and every unsafe mutation requires the established same-origin and CSRF protections.
- [ ] Invalid currency, amount, timezone, or secret configuration fails safely and does not partially update settings.
- [ ] Setting changes affect only future payment and Meeting Details snapshots; historical Booking values never change retroactively.
- [ ] Black-box HTTP tests cover validation, authorization, CSRF/origin enforcement, integer precision, and snapshot boundaries.

