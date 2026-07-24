# 02 — Remove style-prototype from production build

**What to build:** Delete `frontend/src/style-prototype/` (1,048-line CSS +
331-line TSX, "five throwaway directions", currently shipped in the prod bundle)
plus its route glue in `frontend/src/app/Application.tsx` and
`frontend/src/main.tsx`. The folder remains referenceable on the
`archive/style-prototype` branch (already created at main HEAD).

**Blocked by:** None — can start immediately.

**Status:** ready-for-agent

- [ ] `frontend/src/style-prototype/` deleted
- [ ] All imports/routes/regex referencing it removed from `Application.tsx`/`main.tsx`
- [ ] `bun run --cwd frontend build` succeeds; `grep -r style-prototype frontend/dist` finds nothing
- [ ] One commit
