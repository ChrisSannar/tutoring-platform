# 08 — One database session contextmanager

**What to build:** ~65 identical `create_engine` / `try / finally engine.dispose()`
blocks across `backend/app/`. Add one `@contextmanager` in `app/database.py`
(stdlib `contextlib`) yielding a connection/session, and replace every block with
it. Pure mechanical replacement — no transaction semantics change.

**Blocked by:** 03 (touches the merged files)

**Status:** resolved

- [ ] One contextmanager in `app/database.py`
- [ ] All engine/dispose blocks replaced
- [ ] `bun run test:backend` passes
- [ ] One commit
