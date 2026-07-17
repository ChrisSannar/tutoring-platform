# 15 — Retire Session Request and prove the critical journey

**What to build:** Remove the superseded pilot scheduling model and leave one cohesive, responsive Inquiry-to-lesson workflow that is proven from a clean checkout.

**Blocked by:** 03 — One-step Student account claim; 04 — Role-aware manual Login Links; 10 — Tutor Booking calendar and overrides; 11 — Student Booking changes and Calendar Export; 12 — Lesson Note Draft and publication; 14 — Refund Request review.

**Status:** resolved

- [x] Session Request routes, persistence, statuses, service selector, and Student/Tutor UI are removed only after direct Booking behavior is proven.
- [x] No historical Session Request is inferred to be a paid or confirmed Booking; disposable pilot data is handled through an explicit schema transition or documented reset.
- [x] Existing Account, Student Session, authorization, liveness, readiness, error, request-ID, and security-header contracts remain intact.
- [x] The Student Dashboard presents static welcome guidance and a responsive calendar/Shared Lesson Notes layout: notes left and calendar right on desktop, calendar before notes on smaller screens.
- [x] The Tutor Dashboard presents Student search/list left, weekly calendar right, and the active Inquiry and Login Request work queues below without duplicate scheduling models.
- [x] One Playwright critical journey proves Inquiry submission, Tutor Invitation creation/copy, scanner-safe setup, Create Account, promotion-funded Booking, Tutor Booking visibility, Past Booking note publication, and Student note reading/download.
- [x] Browser coverage also proves role-aware landing navigation and manual Login Request delivery where returning access is required.
- [x] The journey uses isolated migrated state, owns both application processes, and requires no mail, Stripe, calendar-provider, or other external network service.
- [x] The authoritative repository test command passes from a clean checkout with deterministic process and database lifecycle.
- [x] Product and domain documentation describe direct Booking as the sole scheduling model and retain Session Request only as clearly labeled historical evidence where needed.

## Answer

Direct Booking is now the only scheduling model. Migration `20260717_0017` explicitly
drops disposable historical Session Request rows without creating Bookings, and the old
routes, implementation, service selector, tests, and Student/Tutor UI are gone. The
responsive Student and Tutor workspace layouts preserve mobile reading order and the
specified desktop pairings. A fresh migrated Playwright journey now proves the complete
Inquiry-to-published-note workflow, while the remaining browser suite covers role-aware
landing navigation and manually delivered returning access. Randomized ports, temporary
SQLite state, owned processes, deterministic providers, and a Tutor-authenticated
test-only clock keep the repository command self-contained.
