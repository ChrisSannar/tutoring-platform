# 04 — Enforce the canonical Invitation lifecycle

**What to build:** Give every Invitation one canonical, evidence-backed lifecycle so Tutor inspection, Invitee opening, claim, expiration, regeneration, and revocation cannot disagree about its state.

**Blocked by:** 03 — Retire the legacy Invitation Claim ceremony.

**Status:** resolved

- [x] Runtime behavior accepts only `created`, `opened`, `claimed`, `expired`, and `revoked` Invitation states.
- [x] Any remaining historical `draft` or `active` records are handled through an explicit, safe schema transition rather than permanent compatibility branches.
- [x] Every lazy-expiration path atomically records `expired`, sets `expired_at`, and erases both lookup and retrievable token material.
- [x] Claimed, expired, and revoked states remain terminal; opening remains observational and never extends expiration.
- [x] Allowed transitions and their required timestamps are centralized so routes and persistence code cannot invent separate lifecycle rules.
- [x] Migration, black-box lifecycle, and concurrency coverage prove the canonical transitions and evidence fields.

## Answer

Invitation persistence now accepts only the canonical lifecycle. The schema transition
maps usable historical `active` rows to `created`, safely revokes legacy `draft` or
incomplete usable rows, expires overdue rows, backfills lifecycle evidence, enforces
canonical state and evidence constraints, and removes the retired Invitation Claim token
table. Runtime response models no longer accept `draft` or `active` Invitation states.

Creation, opening, claim, expiration, regeneration, and revocation now record their
required timestamps atomically. Every interaction lazily persists an overdue Invitation
as `expired` while erasing both lookup and retrievable token material. Opening preserves
the original deadline and first-open evidence; revocation is idempotent; claimed,
expired, and revoked records reject later mutations with sanitized conflicts.

Tutor inspection exposes lifecycle timestamps without exposing token material. Migration
coverage proves safe historical conversion and rejects new legacy states. Black-box HTTP
coverage proves the lifecycle and every lazy-expiration entry point. A synchronized live
two-worker claim-versus-revoke test proves exactly one terminal transition wins and that
Tutor inspection reports the winner's matching evidence.

## Comments

- Red: migration coverage failed because lifecycle evidence columns did not exist and the
  obsolete Invitation Claim token table remained.
- Red: runtime creation violated the new required `created_at` field; claim violated the
  required `claimed_at` evidence constraint.
- Red: link retrieval attempted incomplete expiration, leaving lookup material and no
  `expired_at`; terminal retries returned `404` instead of idempotent success or a
  sanitized `409` conflict.
- Red: the first authoritative run passed 97 of 99 backend tests and exposed obsolete
  pilot-data cleanup SQL against the retired claim-token table.
- Green: 35 Invitation-focused migration, lifecycle, claim, module-size, and live
  concurrency tests passed.
- Green: the authoritative backend suite passed 99 tests and the Playwright suite passed
  all 13 tests using the documented `/tmp` environment shims.
- Environment: the live concurrency test required localhost socket access; its initial
  sandboxed run failed with `PermissionError`, then passed with socket access enabled.
- Review remediation red: a migration test covering every runtime-recognized historical
  state plus an arbitrary schema-valid state failed because the unknown state reached
  the canonical-status constraint; the migration also fabricated lifecycle times.
- Review remediation green: complete usable rows remain usable, due rows expire, and
  incomplete or unknown rows revoke fail-closed. Existing terminal states keep nullable
  unknown historical times, terminal tokens are erased, and no creation/open/claim/
  expiration/revocation timestamp is invented. `USABLE_INVITATION_STATUSES` now matches
  canonical domain language. The 34 targeted tests, all 100 backend tests, and all 15
  Playwright tests passed.
