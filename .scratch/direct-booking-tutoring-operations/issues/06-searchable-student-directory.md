# 06 — Searchable Student directory

**What to build:** Give the Tutor a compact Student directory and one explicit Student Detail surface for operating an established tutoring relationship without allowing casual identity changes.

**Blocked by:** 03 — One-step Student account claim.

**Status:** resolved

- [x] The Tutor Dashboard shows a searchable Student list using the canonical Student identity fields.
- [x] Search narrows the visible list without exposing Students to anonymous or Student callers.
- [x] Selecting a Student opens one Student Detail modal; merely highlighting a Student does not open it.
- [x] The modal displays name and login email as read-only values.
- [x] The modal provides bounded summaries for promotion state, available Session Credits, pending Refund Requests, and the single Upcoming Booking, even when those capabilities have no records yet.
- [x] Tutor responses use explicit allowlists and exclude authentication, token, private log, and unrelated Student data.
- [x] Browser coverage verifies search, selection, modal behavior, read-only identity, empty states, and keyboard-accessible dismissal.
- [x] Black-box tests prove Tutor-only access and cross-Student data isolation.

## Answer

Implemented the Tutor-only Student list and explicit Student Detail boundary. Search is
case-insensitive across canonical name/email identity; selecting a result fetches one
allowlisted detail response and opens a keyboard-dismissible modal with read-only
identity plus bounded promotion, Session Credit, Refund Request, and Upcoming Booking
summaries.

Anonymous and Student sessions cannot read the list or another Student's detail. The
full gate passes with 85 backend tests, 12 Playwright tests, and the production frontend
build. See the Ticket 06 entry in `../map.md`.
