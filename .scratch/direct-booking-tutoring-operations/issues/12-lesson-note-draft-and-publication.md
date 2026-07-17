# 12 — Lesson Note Draft and publication

**What to build:** Let the Tutor prepare lesson material privately for a Past Booking, publish it deliberately, and give the Student one safe accordion and Markdown download for shared session history.

**Blocked by:** 06 — Searchable Student directory; 09 — Promotion, credit, and complimentary Booking.

**Status:** ready-for-agent

- [ ] A non-canceled Booking becomes note-eligible only after its 60-minute end; no separate completion action is introduced.
- [ ] From Student Detail, the Tutor can create and edit one clearly labeled Lesson Note Draft for an eligible Past Booking.
- [ ] A note requires a Tutor-authored title and Markdown source no larger than 100 KB; attachments are not accepted.
- [ ] Saving a draft never exposes it to the Student, and only explicit **Publish** creates the Shared Lesson Note.
- [ ] Later Tutor edits update the same Shared Lesson Note and its downloadable source.
- [ ] Confirmed deletion removes Student access while preserving whatever non-deletable evidence the retention policy requires.
- [ ] The Student Dashboard shows only published notes in one accordion identified by the fixed Booking date and title.
- [ ] Expanded content uses safely rendered Markdown with raw HTML disabled or sanitized and scrolls within a bounded region.
- [ ] The Student can download the original Markdown with a stable date-and-title filename.
- [ ] Tests cover Past Booking derivation, canceled Booking rejection, draft privacy, explicit publication, sanitization, size/title limits, ownership, editing, deletion, and download behavior.

