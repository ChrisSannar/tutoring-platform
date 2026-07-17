# Post-Pilot Implementation Assessment

**Date:** 2026-07-17

This assessment maps the product flow settled in `PRODUCT-GRILLING.md` onto the live
pilot implementation. It is a planning document, not authorization to implement all
slices at once.

## Outcome

The repository should evolve in place. Its application foundation is strong enough to
reuse, but the post-pilot product is materially larger than the current feature set.
Keep the React/FastAPI/SQLite monorepo and deepen it through cohesive domain modules;
microservices, a second origin, a generic calendar-sync layer, and a general payment
wallet are not warranted.

The highest complexity is not the calendar UI. It is maintaining one atomic and
auditable answer to three questions under retries and concurrency:

1. Is this 60-minute slot still available?
2. What funds this Booking: promotion, Session Credit, Stripe payment, or Tutor comp?
3. What value is restored, frozen, forfeited, or refunded after a change?

## Existing foundation to keep

### Keep with little change

- Root Bun orchestration, locked dependencies, isolated Alembic migration flow, and the
  Playwright-owned local application lifecycle.
- FastAPI application construction, typed settings, SQLite boundary validation,
  readiness/liveness probes, sanitized error envelopes, request IDs, and browser
  security headers.
- Opaque server-side sessions, inactivity and absolute expiration, session rotation,
  logout/revocation, same-origin mutation checks, and CSRF protection.
- Account roles, the single-Tutor bootstrap constraint, normalized unique email, and
  Student-owned authorization boundaries.
- Black-box HTTP tests plus one Playwright critical journey as the two primary test
  seams.

### Adapt rather than replace

- **Login Links:** retain hashing, single use, confirmation-before-consumption, rate
  limits, role return, and session creation. Replace immediate development-outbox
  issuance with a persisted Login Request queue and Tutor-triggered issuance. Add the
  repository command for Tutor self-login and use a role-neutral confirmation route.
- **Invitations:** retain normalized email binding, expiration, regeneration,
  revocation, safe public responses, and atomic claim. Collapse draft/activate and the
  second verification token into one active Invitation Link. Add encrypted Tutor
  retrieval until claim and erase encrypted token material at every terminal state.
- **Invitation Claim:** reuse the existing atomic account-plus-session transaction and
  its concurrency tests. Feed it the Invitation Link directly and collect only display
  name plus read-only email.
- **Session Request code:** reuse its Student ownership lookup, UTC normalization,
  per-Student idempotency shape, Tutor visibility query pattern, and negative tests.
  Do not preserve the Session Request table, endpoints, status, service selector, or
  pending-request UI as a second scheduling model.
- **Pilot data deletion:** reuse its explicit confirmation and authorization patterns,
  but redesign retention before deleting payment or credit-ledger evidence.

### Replace at the product surface

- The landing page mail link becomes the Request tutoring modal plus role-aware
  Log In/Dashboard utility.
- TutorAuthentication becomes a shared login-confirmation surface; the Tutor Dashboard
  gets Login Requests, Students, weekly availability/Bookings, Inquiries, settings,
  Refund Requests, and Student Detail.
- InvitationManager loses display-name/message/private-note authoring and the exposed
  draft/activate ceremony.
- StudentWorkspace loses Session Request fields and becomes the calendar/Booking plus
  Shared Lesson Notes dashboard.
- The existing end-to-end journey must be rewritten around Inquiry -> Invitation Link
  -> Create Account -> direct Booking -> Tutor visibility.

## New domain persistence

Expect new schema authority for these cohesive records:

- Inquiries and their optional linked Invitation.
- Login Requests.
- Encrypted Invitation token material and lifecycle evidence.
- Tutor settings: USD Session Price, Tutor Timezone, and default remote Meeting Details.
- Recurring Availability Windows and one-off Blocked Time.
- Slot Holds and processed Stripe webhook events.
- Bookings with funding snapshot, Booking Focus, Meeting Details, cancellation state,
  and original/rescheduled timing evidence.
- Credit Ledger entries, including First Session Promotion and frozen refund value.
- Refund Requests.
- Lesson Note Drafts and published Shared Lesson Notes linked to Past Bookings.

Do not represent funding with only a mutable `credit_balance` column. The immutable
Credit Ledger is the source of truth; a cached balance may be added only if derived and
verified against it.

## Complexity by capability

| Capability | Complexity | Why |
| --- | --- | --- |
| Landing Inquiry and modal | Low-medium | Anonymous validation, rate limiting, Tutor-only content |
| Manual Login Request queue | Medium | Enumeration safety, delayed token issuance, Tutor bootstrap escape hatch |
| Simplified Invitation Claim | Medium | Existing atomic seam is strong; encrypted redisplay adds key management |
| Student/Tutor dashboard shells | Medium | New responsive composition and role-owned queries |
| Shared Lesson Notes and Markdown export | Medium | Draft/publish boundary, safe rendering, ownership, generated download |
| Availability and derived slots | Medium-high | Recurrence, Blocked Time, horizon rules, one-upcoming constraint |
| Booking plus Credit Ledger | High | Atomic slot/funding changes and cancellation restoration/forfeiture |
| Stripe Checkout and refunds | High | 30-minute holds, verified idempotent webhooks, reconciliation, frozen credits |
| `.ics` Calendar Export | Low | Server-generated snapshot; no provider synchronization |

## Recommended TDD slices

Each slice should end with black-box HTTP tests, the applicable Playwright path, the
security completion gate, and its own commit.

1. **Current-flow contract and schema transition plan**
   - Freeze the new direct-Booking journey in a new local spec and ticket queue.
   - Decide whether old pilot rows need migration or may be discarded before changing
     the Session Request and Invitation schemas.
2. **Public Inquiry vertical slice**
   - Request tutoring modal, anonymous validation/rate limiting, New Inquiry list,
     archive/delete, and explicit public/private response tests.
3. **One-step Invitation Link and account claim**
   - Direct active creation from Inquiry or manual email, encrypted redisplay,
     regeneration/revocation, scanner-safe setup, atomic Create Account, and automatic
     First Session Promotion ledger entry.
4. **Manual role-aware Login Links**
   - Generic public Login Request, Tutor queue, delayed 15-minute token generation,
     role-neutral confirmation, Dashboard routing, and Tutor CLI escape hatch.
5. **Tutor settings and Student directory**
   - Price, timezone, default remote details, searchable Student list, read-only detail
     modal, credit/promotion display, and calendar-to-list selection behavior.
6. **Availability engine**
   - Recurring windows, Blocked Time, 60-minute derived slots, 24-hour/eight-week limits,
     conflict checks, and Tutor Override outside normal windows.
7. **Promotion, Credit Ledger, and complimentary Booking**
   - Ledger invariants, reasoned Tutor adjustments, one-upcoming constraint, atomic
     promotion/credit funding, Booking Focus, and Tutor-created complimentary Booking.
8. **Student Booking calendar without Stripe**
   - Select slot, confirmation modal, promotion/credit booking, full own-Booking detail,
     private treatment of other calendar occupancy, and Tutor calendar visibility.
9. **Rescheduling, cancellation, and Calendar Export**
   - 24-hour rules, funding preservation/restoration/forfeiture, Tutor Overrides,
     editable Meeting Details, and stable `.ics` download.
10. **Lesson Note Draft and publish flow**
    - Past Booking eligibility, Tutor CRUD, explicit publish, Student accordion, safe
      Markdown rendering, 100 KB boundary, and raw `.md` download.
11. **Stripe Checkout, Slot Holds, and webhook fulfillment**
    - Server-owned price, 30-minute holds, Checkout creation, idempotent verified
      webhook processing, successful Booking conversion, expiration cleanup, and
      failure/retry tests.
12. **Refund Requests and reconciliation**
    - Early-cancellation replacement credit, frozen value, Tutor approve/decline,
      full Stripe refund, double-value prevention, and operational reconciliation.
13. **Remove superseded pilot flow and finish the critical E2E**
    - Remove Session Request routes/UI/schema only after direct Booking is proven.
    - Replace historical E2E assertions and verify the complete new journey.

## Sequencing guidance

Slices 2 through 4 may share the existing authentication and Invitation foundation, but
land them in order because the E2E journey depends on their final contracts. Slices 5
and 6 can be developed independently after Tutor authentication is stable. Slices 7 and
8 are sequential because Booking must consume the ledger transactionally. Notes can
start after the Booking identity and Past Booking rule exist. Stripe should follow the
promotion/credit Booking path so payment adds one funding adapter rather than defining
Booking itself. Refunds must follow Stripe.

## Architectural decisions worth recording before implementation

Two accepted trade-offs meet the threshold for short ADRs:

- Invitation Links remain retrievable until claim using encryption, trading additional
  key management for Tutor convenience.
- Stripe webhook fulfillment, not browser redirect, is authoritative for paid Booking
  creation, with a 30-minute Slot Hold protecting availability.

## Verification snapshot

- Live repository size inspected: approximately 5,600 lines across application, tests,
  and E2E TypeScript/Python files.
- Backend baseline: 63 tests passed on 2026-07-17 when run with loopback access.
- Full E2E was not rerun because an existing `uvicorn` process (PID 2029569) owns port
  `7311`; it was left untouched.
- Only product/domain documentation was changed during this session.
