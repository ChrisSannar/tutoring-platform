# 01 — Drop module-size enforcement, keep the principle

**What to build:** Delete `backend/tests/test_module_sizes.py` (asserts every app
module < 100 lines — the root cause of 115 tiny files). Record the principle in
`AGENTS.md`: modules should strive to stay small/cohesive (~100 lines as a
guideline), but the guideline may be broken when a cohesive module needs more.
Also delete the dead `backend/app/session_requests/` package (only `__pycache__`,
zero imports).

**Blocked by:** None — can start immediately.

**Status:** resolved

- [x] `backend/tests/test_module_sizes.py` deleted
- [x] `AGENTS.md` records the small-module principle as a guideline, not a rule
- [x] `backend/app/session_requests/` deleted
- [x] `bun run test:backend` passes
- [x] One commit

## Answer

Commit `44083b4 Drop module-size enforcement, keep the principle`.

- Verified zero imports of `app.session_requests` (only migration history and a
  retirement test reference the table name) before deleting the directory.
- `AGENTS.md` gained a "Module size" section: ~100 lines as a guideline,
  phrased as a principle that may yield to genuine cohesion.
- Tests: 100 → 99 (the deleted module-size test was the delta). Suite green via
  `UV_CACHE_DIR=/tmp/tutoring-platform-uv-cache uv run --project backend --group test pytest backend/tests -q`.
