# 05 — Redesign Invitation setup

Type: task
Status: resolved
Blocked by: 04

## What to build

Compose Invitation setup, loading, and unavailable states as a restrained
single-task Constellation surface using shared primitives.

## Constraints

- Preserve every word, action, API call, label, accessibility relationship, and state.
- No generic wrapper or raw theme colors.

## Acceptance

- [x] Invitation setup and unavailable/loading states work in both themes.
- [x] Keyboard focus remains visible.
- [x] No horizontal overflow at `390px`, `800px`, or `1280px`.
- [x] Frontend build and closest critical-journey Playwright coverage pass.
- [x] One commit.

## Comments

## Answer

- Reused `main.login-authentication` for setup, loading, and unavailable states;
  no new wrapper, dependency, stylesheet rule, copy, action, or API behavior.
- `bun run build` passed.
- `bun run test:e2e -- e2e/tutor-authentication.spec.ts
  e2e/critical-journey.spec.ts` passed: 9 tests.
- Playwright checks both themes for every Invitation state, visible keyboard focus
  on Display name, and no horizontal overflow at `390px`, `800px`, or `1280px`.
- Kept as one issue-scoped change for the rollout commit.
