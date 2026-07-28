# 04 — Redesign Tutor access states

Type: task
Status: resolved
Blocked by: 03

## What to build

Compose Tutor sign-in and confirmation states as a restrained single-task
Constellation surface. Preserve the transition into the existing Tutor workspace.

## Constraints

- Preserve every word, action, API call, label, and conditional state.
- Keep the footer visible during access states and hidden in the authenticated workspace.
- No generic wrapper or raw theme colors.

## Acceptance

- [x] Tutor access states match the shared visual language in both themes.
- [x] Keyboard focus and footer behavior remain correct.
- [x] No horizontal overflow at `390px`, `800px`, or `1280px`.
- [x] Frontend build and Tutor authentication Playwright coverage pass.
- [x] One commit.

## Comments

## Answer

Tutor sign-in, link-sent, loading, and confirmation states now reuse the shared
`login-authentication` surface without redundant wrappers. Existing copy, actions,
API calls, accessibility relationships, state transitions, and the authenticated
Tutor workspace remain unchanged.

Evidence:

- `bun run build` — passed; 51 modules transformed.
- `bun run test:e2e -- tutor-authentication.spec.ts` — passed; 7 tests.
- Playwright verifies both themes, visible input focus, access-state footer
  visibility, workspace footer hiding, and no horizontal overflow at `390px`,
  `800px`, and `1280px`.
- Commit boundary is issue 04 only; the parent agent owns the single commit.

Context: [Application-wide Constellation rollout](../spec.md).
