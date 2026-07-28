# 07 — Consolidate backend test setup into conftest fixtures

**What to build:** 16 of 20 test files re-implement the same ~15-line setup:
alembic upgrade to tmp sqlite, `monkeypatch.setenv` ×3–4,
`get_settings.cache_clear()` (93 call sites), `AsyncClient(ASGITransport(create_app()))`,
and the magic-link auth dance. Move to `backend/tests/conftest.py` (currently 14
lines) as fixtures, e.g. `client` and an authenticated `tutor_client`; rewrite the
test files to use them. Keep per-test env overrides working (fixtures may accept
`monkeypatch` parametrically or expose a `make_client` factory — pick the laziest
shape that keeps every test passing unchanged in intent).

**Blocked by:** 03 (test files touch merged modules' imports)

**Status:** resolved

- [ ] `conftest.py` owns shared setup; duplicated setup deleted from test files
- [ ] No test's intent changed — mechanical replacement only
- [ ] `bun run test:backend` passes with same test count
- [ ] One commit
