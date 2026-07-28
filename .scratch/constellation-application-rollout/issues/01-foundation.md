# 01 — Centralize the Constellation foundation

Type: task
Status: ready-for-agent
Blocked by: None

## What to build

Promote Constellation light/dark semantic tokens to `:root` in
`frontend/src/styles.css`. Make shared buttons, links, fields, dialogs, sections,
focus states, canvas treatment, and square geometry consume them. Remove duplicated
Tutor-only token values without changing the `/tutor` reference layout. Update
`docs/DESIGN-STANDARD.md` to authorize application-wide adoption and distinguish
full-workspace dotted canvases from quieter focused pages.

## Constraints

- No new dependency, component abstraction, route, copy, or behavior change.
- Component rules must not introduce raw theme colors.

## Acceptance

- [ ] Shared semantic tokens support equivalent light/dark hierarchy.
- [ ] `/tutor` retains its layout and visible focus behavior.
- [ ] Design standard records application-wide authorization.
- [ ] Frontend build and focused Tutor overview/authentication tests pass.
- [ ] One commit.

## Comments

