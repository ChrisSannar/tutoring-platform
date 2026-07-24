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

**Status:** resolved

- [x] All four cuts applied; build succeeds
- [x] `bun run test:e2e` passes
- [x] One commit

## Answer

1. `students-changed` listener removed from `StudentList.tsx`; fetch inlined.
2. `students/types.ts` and `invitations/types.ts` inlined into their sole
   consumers; files deleted.
3. Unused `initialStudent` prop removed from `StudentWorkspace.tsx`.
4. `theme`/`onThemeToggle` drilling removed (`main.tsx` → `Application.tsx` →
   `TutorAuthentication.tsx` → `TutorWorkspace.tsx`); the rail toggle now owns
   local state and writes `localStorage` + `documentElement.dataset.theme`
   directly (marked with a `ponytail:` comment). Footer toggle reads
   `dataset.theme` on click so it stays correct after rail toggles.
Build + e2e pass. Commit `774e639`.
