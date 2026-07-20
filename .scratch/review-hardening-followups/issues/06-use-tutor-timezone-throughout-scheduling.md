# 06 — Use Tutor Timezone throughout Tutor scheduling

**What to build:** Let the Tutor view and edit all scheduling wall times in the configured Tutor Timezone regardless of the browser device timezone.

**Blocked by:** None — can start immediately.

**Status:** resolved

- [x] The Tutor Booking calendar labels and renders Booking times in the configured Tutor Timezone.
- [x] Moving a Booking interprets datetime-local input in the Tutor Timezone before sending the authoritative instant to the server.
- [x] Blocked Time and Tutor Override creation and editing use the same Tutor Timezone conversion rather than the browser timezone.
- [x] Changing the browser timezone does not change the wall time shown for the same Tutor scheduling record.
- [x] Tests cover a browser timezone different from the Tutor Timezone and at least one daylight-saving boundary.
- [x] Student-visible Tutor Timezone behavior and the authoritative repository test command remain green.

## Answer

Tutor scheduling now formats authoritative instants and interprets `datetime-local`
values in the configured Tutor Timezone. The shared conversion is used by the Booking
calendar, Booking moves, Blocked Time creation and editing, Tutor Override creation,
and complimentary Booking creation. Changing Tutor Timezone remounts scheduling views
with the newly saved setting.

The public Tutor Override edit flow is the documented selection of an Override while
moving an existing Tutor-created Booking; standalone Override records support creation,
selection, and deletion, not in-place editing. Playwright covers that mapping through
the Booking schedule endpoint.

## Comments

- Red: in an `Asia/Tokyo` browser with Tutor Timezone `America/New_York`, the Booking
  after New York's fall-back rendered `11/3/2026, 12:00:00 AM` instead of
  `11/2/2026, 10:00:00 AM`.
- Green: the targeted Playwright test passed 1 test. It proved the 10:00 New York
  Booking label and move, Blocked Time create/edit, Tutor Override create/use, and
  complimentary Booking creation from a Tokyo browser.
- DST proof: `2026-11-09T10:00` New York became `2026-11-09T15:00:00Z` after fall-back;
  `2027-03-15T10:00` became `2027-03-15T14:00:00Z` after spring-forward.
- Green: the authoritative command passed 100 backend tests and 15 Playwright tests:
  `BUN_INSTALL=/tmp/bun BUN_TMPDIR=/tmp UV_CACHE_DIR=/tmp/tutoring-platform-uv-cache PLAYWRIGHT_BROWSERS_PATH=/tmp/tutoring-platform-playwright bun run test`.
