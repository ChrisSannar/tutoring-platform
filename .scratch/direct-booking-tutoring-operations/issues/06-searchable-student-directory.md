# 06 — Searchable Student directory

**What to build:** Give the Tutor a compact Student directory and one explicit Student Detail surface for operating an established tutoring relationship without allowing casual identity changes.

**Blocked by:** 03 — One-step Student account claim.

**Status:** ready-for-agent

- [ ] The Tutor Dashboard shows a searchable Student list using the canonical Student identity fields.
- [ ] Search narrows the visible list without exposing Students to anonymous or Student callers.
- [ ] Selecting a Student opens one Student Detail modal; merely highlighting a Student does not open it.
- [ ] The modal displays name and login email as read-only values.
- [ ] The modal provides bounded summaries for promotion state, available Session Credits, pending Refund Requests, and the single Upcoming Booking, even when those capabilities have no records yet.
- [ ] Tutor responses use explicit allowlists and exclude authentication, token, private log, and unrelated Student data.
- [ ] Browser coverage verifies search, selection, modal behavior, read-only identity, empty states, and keyboard-accessible dismissal.
- [ ] Black-box tests prove Tutor-only access and cross-Student data isolation.

