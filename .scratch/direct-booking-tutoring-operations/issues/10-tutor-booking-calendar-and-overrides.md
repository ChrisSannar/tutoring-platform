# 10 — Tutor Booking calendar and overrides

**What to build:** Turn the Tutor's weekly calendar into an operational view of every Booking and a wayfinder into the correct Student relationship, while preserving Tutor scheduling authority.

**Blocked by:** 06 — Searchable Student directory; 09 — Promotion, credit, and complimentary Booking.

**Status:** ready-for-agent

- [ ] The Tutor weekly calendar displays all Bookings with enough information to operate the schedule.
- [ ] Selecting a Booking highlights and scrolls to its Student in the list without opening Student Detail automatically.
- [ ] Selecting the highlighted Student explicitly opens Student Detail with the Upcoming Booking in context.
- [ ] The Tutor can edit a Booking's Meeting Details, including replacing remote instructions with an address for an exceptional arrangement.
- [ ] The Tutor can move a Booking to an otherwise-free normal Bookable Slot without changing its original funding.
- [ ] The Tutor can deliberately override availability or horizon limits after a clear warning, provided the full interval is otherwise unoccupied.
- [ ] Tutor-initiated changes preserve Student funding by default and never apply a late-change penalty implicitly.
- [ ] Browser tests verify calendar-to-list highlighting, scrolling, explicit modal behavior, and warned overrides.
- [ ] Black-box tests cover conflict rejection, funding preservation, snapshot edits, Tutor-only authorization, and private response boundaries.

