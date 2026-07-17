# 12 — Lesson Note Draft and publication

**What to build:** Let the Tutor prepare lesson material privately for a Past Booking, publish it deliberately, and give the Student one safe accordion and Markdown download for shared session history.

**Blocked by:** 06 — Searchable Student directory; 09 — Promotion, credit, and complimentary Booking.

**Status:** resolved

- [x] A non-canceled Booking becomes note-eligible only after its 60-minute end; no separate completion action is introduced.
- [x] From Student Detail, the Tutor can create and edit one clearly labeled Lesson Note Draft for an eligible Past Booking.
- [x] A note requires a Tutor-authored title and Markdown source no larger than 100 KB; attachments are not accepted.
- [x] Saving a draft never exposes it to the Student, and only explicit **Publish** creates the Shared Lesson Note.
- [x] Later Tutor edits update the same Shared Lesson Note and its downloadable source.
- [x] Confirmed deletion removes Student access while preserving whatever non-deletable evidence the retention policy requires.
- [x] The Student Dashboard shows only published notes in one accordion identified by the fixed Booking date and title.
- [x] Expanded content uses safely rendered Markdown with raw HTML disabled or sanitized and scrolls within a bounded region.
- [x] The Student can download the original Markdown with a stable date-and-title filename.
- [x] Tests cover Past Booking derivation, canceled Booking rejection, draft privacy, explicit publication, sanitization, size/title limits, ownership, editing, deletion, and download behavior.

## Answer

Past, non-canceled Bookings appear in Student Detail as one-note draft workspaces without
a separate completion action. Notes require a visible title and at most 100 KB of
Markdown; extra attachment fields are rejected. Drafts remain Tutor-only until explicit
publication, later saves update the same shared record and download, and confirmed
deletion clears shared content while retaining the evidence shell. Students see only
published notes in date-and-title accordions, rendered through a bounded safe Markdown
subset where raw HTML remains inert text, with stable original-source downloads.
