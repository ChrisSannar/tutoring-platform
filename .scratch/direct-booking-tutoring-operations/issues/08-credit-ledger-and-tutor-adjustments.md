# 08 — Credit Ledger and Tutor adjustments

**What to build:** Give each Student an auditable Session Credit balance derived from immutable events, with controlled Tutor adjustments and clear promotion state.

**Blocked by:** 03 — One-step Student account claim; 06 — Searchable Student directory.

**Status:** resolved

- [x] A Student's available Session Credit balance is derived from immutable Credit Ledger entries rather than an editable balance field.
- [x] The initial First Session Promotion grant is represented distinctly from ordinary Session Credits and is visible in Tutor and Student funding summaries.
- [x] The Tutor can grant or deduct Session Credits from Student Detail only with a required short reason.
- [x] Adjustments append ledger evidence without rewriting or deleting prior events.
- [x] A deduction cannot make available value negative, and retries cannot apply the same adjustment more than once.
- [x] Ledger responses disclose only the minimum funding information appropriate to the authenticated role.
- [x] Credit operations require Tutor authorization, same-origin validation, CSRF protection, and idempotency where a retry could duplicate value.
- [x] Black-box tests cover grants, deductions, reason validation, balance derivation, promotion separation, retries, concurrency, and cross-role denial.

## Answer

Session Credits are now a projection over append-only `credit_*` ledger events; the
First Session Promotion remains a separate promotion event and funding-summary field.
Tutor-only adjustments require a signed quantity, reason, same-origin CSRF evidence,
and an idempotency key. The transaction rejects negative projected balances even under
concurrent deductions, and Student-facing responses expose only the bounded funding
summary. Student Detail provides the adjustment workflow and refreshes the derived
balance. Verification: 88 backend tests and 12 Playwright journeys pass.
