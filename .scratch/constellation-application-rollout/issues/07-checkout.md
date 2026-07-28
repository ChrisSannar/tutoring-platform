# 07 — Redesign Checkout states

Type: task
Status: resolved
Blocked by: 06

## What to build

Compose Checkout loading, status, and unavailable states as a restrained single-task
Constellation surface using shared primitives.

## Constraints

- Preserve every word, link, API call, accessibility relationship, and state.
- No generic wrapper or raw theme colors.

## Acceptance

- [x] Checkout states retain equivalent hierarchy in both themes.
- [x] Keyboard focus remains visible.
- [x] No horizontal overflow at `390px`, `800px`, or `1280px`.
- [x] Frontend build and closest critical-journey Playwright coverage pass.
- [x] Final `bun run build` and full `bun run test` pass.
- [x] One commit.

## Comments

## Answer

- Reused the existing `.login-authentication` surface for Checkout loading,
  status, and unavailable states without changing copy, links, API behavior,
  accessibility relationships, or state branches.
- Added local route-intercepted critical-journey coverage for loading, status,
  unavailable, light/dark surface parity, visible link focus, and no horizontal
  overflow at `390px`, `800px`, and `1280px`.
- No CSS, wrapper, helper, dependency, backend, or public interface changes.
- Evidence:
  - `bun run build` — passed (`tsc -b && vite build`, 51 modules transformed).
  - `bun run test:e2e -- critical-journey.spec.ts` — passed, 2 tests.
  - `bun run test` — passed, 103 backend tests and 23 Playwright tests.
  - `git diff --check` — passed.
- Commit boundary: `CheckoutStatus.tsx`, its focused critical-journey coverage,
  and this ticket; left uncommitted for the coordinating agent's single commit.
