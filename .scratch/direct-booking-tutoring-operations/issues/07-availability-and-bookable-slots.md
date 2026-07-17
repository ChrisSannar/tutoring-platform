# 07 — Availability and Bookable Slots

**What to build:** Let the Tutor define when tutoring can occur and let a Student see only derived, privacy-preserving 60-minute choices that satisfy the initial scheduling policy.

**Blocked by:** 05 — Tutor business settings.

**Status:** ready-for-agent

- [ ] The Tutor can create, edit, and delete recurring weekly Availability Windows through a small calendar interaction.
- [ ] The Tutor can create, edit, and delete date-specific Blocked Time that removes overlapping availability.
- [ ] Bookable Slots are derived as consecutive 60-minute intervals anchored at each Availability Window start; partial leftover time is excluded.
- [ ] Student-visible slots use the labeled Tutor Timezone and fall between the 24-hour minimum notice and eight-week horizon.
- [ ] Bookings, Blocked Time, and active Slot Holds remove overlapping choices without revealing the occupant or reason to a Student.
- [ ] Empty calendar time outside an Availability Window is never selectable.
- [ ] Tutor Overrides can identify an otherwise-free time outside normal availability or horizon rules, but require an explicit warning before later Booking creation.
- [ ] Time-sensitive tests use a controlled clock and cover recurrence, timezone boundaries, anchoring, conflicts, policy boundaries, privacy, and Tutor authorization.

