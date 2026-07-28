# 03 — Redesign role-aware Login

Type: task
Status: resolved
Blocked by: 02

## What to build

Compose role-aware Login and all result states as a restrained single-task
Constellation surface using shared primitives.

## Constraints

- Preserve every word, role choice, action, API call, label, and result state.
- No generic wrapper or raw theme colors.

## Acceptance

- [x] Login and its result states retain equivalent hierarchy in both themes.
- [x] Keyboard focus remains visible.
- [x] No horizontal overflow at `390px`, `800px`, or `1280px`.
- [x] Frontend build and closest authentication Playwright coverage pass.
- [x] One commit.

## Comments

## Answer

- Reused one scoped `login-authentication` class across request, sent, confirm,
  and invalid states without changing copy, roles, actions, API calls, or redirects.
- `bun run build` passed.
- `bun run test:e2e -- e2e/login-request.spec.ts` passed: 2 tests.
- Delivery is one issue-scoped commit.
