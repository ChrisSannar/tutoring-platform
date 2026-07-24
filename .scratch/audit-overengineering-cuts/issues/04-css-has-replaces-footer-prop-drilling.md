# 04 — CSS :has() replaces tutorWorkspaceVisible prop drilling

**What to build:** Delete the `tutorWorkspaceVisible` state + `onTutorWorkspaceChange`
callback + syncing `useEffect` drilled `main.tsx` → `Application.tsx` →
`TutorAuthentication.tsx`. Replace with CSS `:has()` rules in `styles.css`:
`.app-shell:has(.tutor-workspace) .app-footer { display: none }` and the shell
display rule. Update the e2e assertion in `tutor-authentication.spec.ts`
(footer `toHaveCount(0)` → hidden/not visible).

**Blocked by:** 02

**Status:** ready-for-agent

- [ ] State, callback prop chain, and effect deleted
- [ ] Two CSS rules added; footer hides on tutor workspace, shows elsewhere
- [ ] e2e assertion updated; `bun run test:e2e` passes
- [ ] One commit
