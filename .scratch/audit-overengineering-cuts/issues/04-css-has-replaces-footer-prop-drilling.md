# 04 — CSS :has() replaces tutorWorkspaceVisible prop drilling

**What to build:** Delete the `tutorWorkspaceVisible` state + `onTutorWorkspaceChange`
callback + syncing `useEffect` drilled `main.tsx` → `Application.tsx` →
`TutorAuthentication.tsx`. Replace with CSS `:has()` rules in `styles.css`:
`.app-shell:has(.tutor-workspace) .app-footer { display: none }` and the shell
display rule. Update the e2e assertion in `tutor-authentication.spec.ts`
(footer `toHaveCount(0)` → hidden/not visible).

**Blocked by:** 02

**Status:** resolved

- [x] State, callback prop chain, and effect deleted
- [x] Two CSS rules added; footer hides on tutor workspace, shows elsewhere
- [x] e2e assertion updated; `bun run test:e2e` passes
- [x] One commit

## Answer

Deleted `tutorWorkspaceVisible` state in `main.tsx`, the
`onTutorWorkspaceChange` prop chain through `Application.tsx` →
`TutorAuthentication.tsx`, and the syncing effect; footer now always renders.
Added `.app-shell:has(.tutor-workspace) { display: block }` and
`.app-shell:has(.tutor-workspace) .app-footer { display: none }` to
`styles.css` (replacing `.tutor-app-shell`). e2e assertion changed from
`toHaveCount(0)` to `toBeHidden()`. Build + e2e pass. Commit `8ce9dc1`.
