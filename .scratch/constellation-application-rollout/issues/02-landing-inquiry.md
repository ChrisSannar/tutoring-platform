# 02 — Redesign Landing and Inquiry

Type: task
Status: resolved
Blocked by: 01

## What to build

Compose Landing as an editorial bordered surface with a clear action group. Treat the
Inquiry dialog as part of the same surface and use the shared Constellation primitives.

## Constraints

- Preserve every word, action, API call, label, and accessibility relationship.
- No generic wrapper or raw theme colors.

## Acceptance

- [x] Landing and Inquiry have Constellation composition in both themes.
- [x] Keyboard focus remains visible.
- [x] No horizontal overflow at `390px`, `800px`, or `1280px`.
- [x] Frontend build and closest public Playwright coverage pass.
- [x] One commit.

## Comments

## Answer

Composed the Landing actions as a responsive Constellation group and scoped the
shared square dialog, field, control, focus, and semantic theme primitives to its
Inquiry flow without changing copy or behavior.

Verification:

- `bun run build` — passed (`tsc -b && vite build`, 51 modules transformed).
- `bun run test:e2e -- public-application.spec.ts` — passed, 7 tests in 4.5s.
  The sandboxed attempt could not bind a temporary localhost port; the approved
  rerun outside the sandbox passed.
