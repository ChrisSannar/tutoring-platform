# 03 — Test-first merge of fragmented backend modules

**What to build:** Merge the enforced fragmentation in `backend/app/`. TEST-FIRST:
before merging each package, list its public functions, confirm each is exercised
by the existing suite (grep tests for route paths/function names), and ADD tests
for any that are uncovered. Suite must pass before the merge and after. Merges:

- `invitations/` 14 files → one `invitations.py` (or `invitations/` with ≤3 files)
- `bookings/` 10 files → same treatment
- `routes/` 26 files → merge by domain (auth, bookings, invitations, checkout/refunds, tutor-*, system/testing); delete pass-through routers (`auth.py`, `tutor_invitations.py`)
- `models/` 15 files → one `models.py` (or ≤4 domain files); empty `__init__.py` files go
- `http/` package → single `app/http.py`
- Re-export-only `__init__.py` files (~12) deleted; import from concrete modules
- `utc_aware` triplicated in `occupancy.py`, `checkout/status.py`, `checkout/webhooks.py` → one canonical helper

**Blocked by:** 01

**Status:** resolved

- [x] Coverage check written down per package (which functions lacked tests, which tests were added)
- [x] Added tests committed BEFORE the merge commit(s)
- [x] Merges done as pure moves — no logic edits
- [x] `bun run test:backend` passes before and after each merge
- [x] One commit for added tests, one commit per package merge (or one merge commit total if moves are trivially verifiable)

## Answer

**Coverage check (Phase A).** All public functions in `invitations/`,
`bookings/`, `http/`, and all `models/` schemas were already exercised through
HTTP by the existing suite (verified by grepping `backend/tests/` for every
route path and imported name). Four route handlers were NOT covered:

- `GET /api/health` (only polled incidentally by live-server helpers)
- `GET /api/auth/session` (never called)
- `POST /api/testing/clock` (tests mutate `context.now` directly instead)
- `GET /invite/{token}` (tests only used the `/api/invitations/{token}` twin)

Added `backend/tests/test_uncovered_routes.py` with five tests (health ok;
auth/session anonymous 401 + tutor role; testing clock override; invite link
opens invitation), following the existing tmp-sqlite + alembic + AsyncClient
style. Committed first as `cbe2b55` (99 → 104 tests).

**Merges (Phase B), all pure moves:**

- `d6fcc4f` — `http/` → `app/http.py`; `models/` (15 files) → `app/models.py`
- `58ea670` — `invitations/` (14 files) → `app/invitations.py`;
  `bookings/` (10 files) → `app/bookings.py`
- `21c537d` — `routes/` (26 files) → 7 domain files (auth, bookings,
  invitations, checkout+refunds, tutor, lesson_notes, system+testing);
  pass-through routers deleted, `main.py` includes the 7 leaf routers
  directly; triplicated `utc_aware`/`aware` deduped to the canonical helper in
  `occupancy.py` (checkout imports it).

Re-export-only `__init__.py` files for the merged packages deleted; all
imports now point at concrete modules. Suite passed after each merge commit.
Tests: 99 before → 104 after. `backend/app` .py files: 115 → 59.
