# 06 — Redesign the Student workspace

Type: task
Status: resolved
Blocked by: 05

## What to build

Compose `/student` as a full dotted-canvas workspace with a clear identity/header area
and bordered Booking and Shared Lesson Note work areas. Include the full booking flow.

## Constraints

- Preserve every word, action, API call, label, accessibility relationship, and
  conditional state.
- Use existing components and shared primitives; no wrapper abstraction or raw colors.

## Acceptance

- [x] Booking and Shared Lesson Notes retain every state and action.
- [x] Light/dark hierarchy and keyboard focus remain equivalent.
- [x] No horizontal overflow at `390px`, `800px`, or `1280px`.
- [x] Frontend build and critical-journey Playwright coverage pass.
- [x] One commit.

## Comments

## Answer

Redesigned `/student` as a scoped Constellation workspace using the shared semantic
tokens and the existing Booking and Shared Lesson Note components unchanged. The
critical journey now verifies the dotted canvas, bordered light/dark work areas,
visible keyboard focus, and no horizontal overflow at `390px`, `800px`, and `1280px`.

Evidence:

- `bun run build` — passed.
- `bun run test:e2e -- e2e/critical-journey.spec.ts` — 1 passed.
- Prepared as one issue slice for its single commit.
