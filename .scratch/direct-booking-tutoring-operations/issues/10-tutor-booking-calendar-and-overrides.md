# 10 — Tutor Booking calendar and overrides

**What to build:** Turn the Tutor's weekly calendar into an operational view of every Booking and a wayfinder into the correct Student relationship, while preserving Tutor scheduling authority.

**Blocked by:** 06 — Searchable Student directory; 09 — Promotion, credit, and complimentary Booking.

**Status:** resolved

- [x] The Tutor weekly calendar displays all Bookings with enough information to operate the schedule.
- [x] Selecting a Booking highlights and scrolls to its Student in the list without opening Student Detail automatically.
- [x] Selecting the highlighted Student explicitly opens Student Detail with the Upcoming Booking in context.
- [x] The Tutor can edit a Booking's Meeting Details, including replacing remote instructions with an address for an exceptional arrangement.
- [x] The Tutor can move a Booking to an otherwise-free normal Bookable Slot without changing its original funding.
- [x] The Tutor can deliberately override availability or horizon limits after a clear warning, provided the full interval is otherwise unoccupied.
- [x] Tutor-initiated changes preserve Student funding by default and never apply a late-change penalty implicitly.
- [x] Browser tests verify calendar-to-list highlighting, scrolling, explicit modal behavior, and warned overrides.
- [x] Black-box tests cover conflict rejection, funding preservation, snapshot edits, Tutor-only authorization, and private response boundaries.

## Answer

The Tutor workspace now includes an allowlisted weekly Booking calendar. Selecting a
Booking highlights and scrolls to the matching Student row without opening detail; the
Tutor must select that Student explicitly to view the Upcoming Booking context. Meeting
Details can be replaced independently. Normal and acknowledged-Override moves reject
occupied intervals and update only the schedule snapshot, leaving the original funding
kind and ledger event untouched. The complete navigation and warned override behavior
run in Playwright, with authorization, privacy, conflicts, snapshots, and funding
preservation covered through HTTP tests.
