# Direct Booking and Tutoring Operations Map

## Notes

- The authoritative seams are black-box FastAPI HTTP behavior and Playwright browser
  journeys.
- Tickets follow the dependency order recorded in their `Blocked by` fields.

## Decisions-so-far

- Ticket 01 resolved: public Inquiries are separate records, limited to five per hashed
  IP per hour, and exposed only through an allowlisted Tutor queue with archive and
  confirmed deletion. Evidence: `issues/01-public-inquiry-intake-and-tutor-queue.md`.

## Fog

- Ticket 02 must settle encrypted Invitation Link redisplay through its required ADR
  before implementation.
- Payment and Credit Ledger retention rules remain required before production payment
  data is accepted.
