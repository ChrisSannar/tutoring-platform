# 06 — Redesign the Student workspace

Type: task
Status: ready-for-agent
Blocked by: 05

## What to build

Compose `/student` as a full dotted-canvas workspace with a clear identity/header area
and bordered Booking and Shared Lesson Note work areas. Include the full booking flow.

## Constraints

- Preserve every word, action, API call, label, accessibility relationship, and
  conditional state.
- Use existing components and shared primitives; no wrapper abstraction or raw colors.

## Acceptance

- [ ] Booking and Shared Lesson Notes retain every state and action.
- [ ] Light/dark hierarchy and keyboard focus remain equivalent.
- [ ] No horizontal overflow at `390px`, `800px`, or `1280px`.
- [ ] Frontend build and critical-journey Playwright coverage pass.
- [ ] One commit.

## Comments

