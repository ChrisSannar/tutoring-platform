# Implementation Assessment

The smallest viable operating model uses the existing immutable Credit Ledger and lazy
reconciliation. It needs no balance table, scheduler, purchasing adapter, or
notification subsystem.

The three concurrency-sensitive operations use immediate database transactions:

1. Invitation Claim creates the Student and grants one credit.
2. Student Booking confirms the slot and redeems one credit.
3. Past Booking or cancellation records one idempotent replenishment.

Public verification belongs at the HTTP boundary plus one critical browser journey.
The schema and removed routes are also checked for absence.
