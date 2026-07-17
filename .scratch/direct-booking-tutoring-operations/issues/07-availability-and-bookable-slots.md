# 07 — Availability and Bookable Slots

**What to build:** Let the Tutor define when tutoring can occur and let a Student see only derived, privacy-preserving 60-minute choices that satisfy the initial scheduling policy.

**Blocked by:** 05 — Tutor business settings.

**Status:** resolved

- [x] The Tutor can create, edit, and delete recurring weekly Availability Windows through a small calendar interaction.
- [x] The Tutor can create, edit, and delete date-specific Blocked Time that removes overlapping availability.
- [x] Bookable Slots are derived as consecutive 60-minute intervals anchored at each Availability Window start; partial leftover time is excluded.
- [x] Student-visible slots use the labeled Tutor Timezone and fall between the 24-hour minimum notice and eight-week horizon.
- [x] Bookings, Blocked Time, and active Slot Holds remove overlapping choices without revealing the occupant or reason to a Student.
- [x] Empty calendar time outside an Availability Window is never selectable.
- [x] Tutor Overrides can identify an otherwise-free time outside normal availability or horizon rules, but require an explicit warning before later Booking creation.
- [x] Time-sensitive tests use a controlled clock and cover recurrence, timezone boundaries, anchoring, conflicts, policy boundaries, privacy, and Tutor authorization.

## Answer

The Tutor calendar manages recurring windows, private Blocked Time, and explicit
Overrides. Student choices are derived 60-minute intervals in the labeled Tutor
Timezone, constrained by notice and horizon policy and filtered by Bookings, blocks,
and active holds without disclosing why a slot is absent. Override-funded Tutor Booking
requires acknowledgement of its stored warning. Controlled-clock HTTP tests cover the
recurrence, anchoring, boundaries, conflict, privacy, and authorization rules; the
calendar management journey is also exercised in Playwright.
