# 05 — Frontend dead code and prop cuts

**What to build:** Four small cuts, one commit:
1. Delete the `students-changed` window event listener in
   `frontend/src/tutor/StudentList.tsx:29-30` — nothing dispatches it (verified).
2. Inline single-use `frontend/src/students/types.ts` and
   `frontend/src/invitations/types.ts` (3–5 lines each, one importer each) into
   their consumers; delete the files.
3. Delete the unused `initialStudent` prop in
   `frontend/src/students/StudentWorkspace.tsx` (sole caller renders it bare).
4. Stop drilling `theme`/`onThemeToggle` through 4 files
   (`main.tsx` → `Application.tsx` → `TutorAuthentication.tsx` →
   `TutorWorkspace.tsx`); the rail toggle reads/writes the same
   `localStorage` + `dataset.theme` pattern `main.tsx` already uses.

**Blocked by:** 02

**Status:** ready-for-agent

- [ ] All four cuts applied; build succeeds
- [ ] `bun run test:e2e` passes
- [ ] One commit
