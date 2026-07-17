# 08 — Credit Ledger and Tutor adjustments

**What to build:** Give each Student an auditable Session Credit balance derived from immutable events, with controlled Tutor adjustments and clear promotion state.

**Blocked by:** 03 — One-step Student account claim; 06 — Searchable Student directory.

**Status:** ready-for-agent

- [ ] A Student's available Session Credit balance is derived from immutable Credit Ledger entries rather than an editable balance field.
- [ ] The initial First Session Promotion grant is represented distinctly from ordinary Session Credits and is visible in Tutor and Student funding summaries.
- [ ] The Tutor can grant or deduct Session Credits from Student Detail only with a required short reason.
- [ ] Adjustments append ledger evidence without rewriting or deleting prior events.
- [ ] A deduction cannot make available value negative, and retries cannot apply the same adjustment more than once.
- [ ] Ledger responses disclose only the minimum funding information appropriate to the authenticated role.
- [ ] Credit operations require Tutor authorization, same-origin validation, CSRF protection, and idempotency where a retry could duplicate value.
- [ ] Black-box tests cover grants, deductions, reason validation, balance derivation, promotion separation, retries, concurrency, and cross-role denial.

