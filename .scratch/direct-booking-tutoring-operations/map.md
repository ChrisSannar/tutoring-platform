# Direct Booking and Tutoring Operations Map

## Notes

- The authoritative seams are black-box FastAPI HTTP behavior and Playwright browser
  journeys.
- Tickets follow the dependency order recorded in their `Blocked by` fields.

## Decisions-so-far

- Ticket 01 resolved: public Inquiries are separate records, limited to five per hashed
  IP per hour, and exposed only through an allowlisted Tutor queue with archive and
  confirmed deletion. Evidence: `issues/01-public-inquiry-intake-and-tutor-queue.md`.
- Ticket 02 resolved: Invitation Links use hash lookup plus authenticated encrypted
  redisplay material, with one-step manual or Inquiry-linked creation and terminal
  erasure. Evidence: `issues/02-retrievable-invitation-link-management.md` and
  `../../docs/adr/0004-encrypt-retrievable-invitation-links.md`.
- Ticket 03 resolved: the original Invitation Link now supports observational setup
  reads and one atomic Student, Student Session, and First Session Promotion claim;
  linked Inquiries leave active work. Evidence:
  `issues/03-one-step-student-account-claim.md`.
- Ticket 04 resolved: one public role-neutral request flow feeds a Tutor-only Student
  Login Request queue; generated links are short-lived, single-use, role-routed, and
  manually delivered. Evidence: `issues/04-role-aware-manual-login-links.md`.
- Ticket 06 resolved: the Tutor has a searchable allowlisted Student directory and
  explicit read-only Student Detail modal with bounded operational summaries. Evidence:
  `issues/06-searchable-student-directory.md`.
- Ticket 08 resolved: Session Credits are derived from append-only ledger events;
  Tutor adjustments require reasons and idempotency, reject negative concurrent
  deductions, and keep the First Session Promotion distinct. Evidence:
  `issues/08-credit-ledger-and-tutor-adjustments.md`.

## Fog

- Ticket 05 settings are implemented; its non-retroactive Booking/payment and Meeting
  Details snapshot proof remains open until the Booking seam exists.
- Payment retention rules remain required before production payment data is accepted.
