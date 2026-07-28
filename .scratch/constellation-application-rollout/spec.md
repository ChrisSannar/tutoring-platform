# Application-wide Constellation rollout

Status: ready-for-agent

## Goal

Adopt the authenticated `/tutor` Constellation visual language across every
frontend surface while preserving all copy, routes, API behavior, accessibility
relationships, and workflows.

## Scope

- Centralize semantic light/dark colors, square geometry, controls, focus states,
  canvas treatment, and theme behavior in `frontend/src/styles.css`.
- Redesign Landing and Inquiry, role-aware Login, Tutor access, Invitation setup,
  Student workspace and booking, Shared Lesson Notes, and Checkout states.
- Retain the non-Tutor footer and theme control. Keep the footer hidden only in the
  authenticated Tutor workspace.
- Use the dotted canvas for full workspaces and quieter token-compatible backgrounds
  for focused access and payment pages.

## Constraints

- No backend, database, route, copy, workflow, or public TypeScript interface changes.
- No component framework, dependency, generic wrapper, or speculative abstraction.
- Component rules use shared semantic tokens rather than raw theme colors.
- `/tutor` remains the reference layout.

## Ready-for-agent issues

1. Centralize the Constellation foundation and update the design standard.
2. Redesign Landing and its Inquiry dialog.
3. Redesign role-aware Login and its result states.
4. Redesign Tutor sign-in and confirmation states.
5. Redesign Invitation setup and unavailable/loading states.
6. Redesign the Student workspace, booking flow, and Shared Lesson Notes.
7. Redesign Checkout status and unavailable/loading states.

## Verification

- Extend the closest Playwright coverage for each surface to preserve visible
  content/actions, visible keyboard focus, light/dark hierarchy, and no horizontal
  overflow at `390px`, `800px`, and `1280px`.
- Foundation: frontend build plus focused Tutor overview/authentication coverage.
- Each surface: frontend build plus its closest public, authentication, or
  critical-journey coverage.
- Final: `bun run build` and `bun run test`.

