# Spec — Over-engineering audit cuts

Whole-repo ponytail audit (2026-07-24) found ~3,300–3,700 removable lines. This
effort applies the cuts. Over-engineering only — no behavior change intended.

Key constraints from the maintainer:

- The 100-line-per-file cap is a design principle, not an enforced rule. Remove the
  enforcing test, record the principle in `AGENTS.md`. It may be broken when a
  cohesive module needs it.
- Module merges are test-first: every public function in a merged module must have
  test coverage before the merge; the suite must pass before and after.
- `frontend/src/style-prototype/` leaves production but is preserved on the
  `archive/style-prototype` branch.

Sections execute in order — Structural, Frontend, Backend — one commit per ticket.
All work on branch `refactor/audit-cuts`.

Verification: `bun run test:backend` after backend tickets; `bun run test:e2e`
after frontend tickets.
