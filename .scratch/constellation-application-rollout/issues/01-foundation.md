# 01 — Centralize the Constellation foundation

Type: task
Status: resolved
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

- [x] Shared semantic tokens support equivalent light/dark hierarchy.
- [x] `/tutor` retains its layout and visible focus behavior.
- [x] Design standard records application-wide authorization.
- [x] Frontend build and focused Tutor overview/authentication tests pass.
- [x] One commit.

## Comments

## Answer

Centralized the approved Constellation light/dark tokens in `:root`, moved shared
surfaces and controls onto them, and removed the duplicate Tutor-only palette while
preserving the Tutor layout, responsive behavior, colors, and focus treatment.
Authorized application-wide adoption in the design standard and distinguished dotted
full workspaces from quieter focused pages.

Verification:

- `bun run build` — passed (`tsc -b && vite build`, 51 modules transformed).
- `bun run test:e2e -- tutor-overview.spec.ts tutor-authentication.spec.ts` — passed,
  9 tests in 9.4s. The sandboxed attempt could not bind a temporary localhost port;
  the approved rerun outside the sandbox passed.
