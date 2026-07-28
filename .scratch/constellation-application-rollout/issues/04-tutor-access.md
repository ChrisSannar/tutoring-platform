# 04 — Redesign Tutor access states

Type: task
Status: ready-for-agent
Blocked by: 03

## What to build

Compose Tutor sign-in and confirmation states as a restrained single-task
Constellation surface. Preserve the transition into the existing Tutor workspace.

## Constraints

- Preserve every word, action, API call, label, and conditional state.
- Keep the footer visible during access states and hidden in the authenticated workspace.
- No generic wrapper or raw theme colors.

## Acceptance

- [ ] Tutor access states match the shared visual language in both themes.
- [ ] Keyboard focus and footer behavior remain correct.
- [ ] No horizontal overflow at `390px`, `800px`, or `1280px`.
- [ ] Frontend build and Tutor authentication Playwright coverage pass.
- [ ] One commit.

## Comments

