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

**Status:** ready-for-agent

- [ ] Coverage check written down per package (which functions lacked tests, which tests were added)
- [ ] Added tests committed BEFORE the merge commit(s)
- [ ] Merges done as pure moves — no logic edits
- [ ] `bun run test:backend` passes before and after each merge
- [ ] One commit for added tests, one commit per package merge (or one merge commit total if moves are trivially verifiable)
