# 07 — Redesign Checkout states

Type: task
Status: ready-for-agent
Blocked by: 06

## What to build

Compose Checkout loading, status, and unavailable states as a restrained single-task
Constellation surface using shared primitives.

## Constraints

- Preserve every word, link, API call, accessibility relationship, and state.
- No generic wrapper or raw theme colors.

## Acceptance

- [ ] Checkout states retain equivalent hierarchy in both themes.
- [ ] Keyboard focus remains visible.
- [ ] No horizontal overflow at `390px`, `800px`, or `1280px`.
- [ ] Frontend build and closest critical-journey Playwright coverage pass.
- [ ] Final `bun run build` and full `bun run test` pass.
- [ ] One commit.

## Comments

