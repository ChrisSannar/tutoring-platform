# 01 — Drop module-size enforcement, keep the principle

**What to build:** Delete `backend/tests/test_module_sizes.py` (asserts every app
module < 100 lines — the root cause of 115 tiny files). Record the principle in
`AGENTS.md`: modules should strive to stay small/cohesive (~100 lines as a
guideline), but the guideline may be broken when a cohesive module needs more.
Also delete the dead `backend/app/session_requests/` package (only `__pycache__`,
zero imports).

**Blocked by:** None — can start immediately.

**Status:** ready-for-agent

- [ ] `backend/tests/test_module_sizes.py` deleted
- [ ] `AGENTS.md` records the small-module principle as a guideline, not a rule
- [ ] `backend/app/session_requests/` deleted
- [ ] `bun run test:backend` passes
- [ ] One commit
