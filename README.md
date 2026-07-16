# Tutoring Platform

**Dates:** 2026-07-15 through 2026-07-17

**Target:** 30 focused hours across three days

**Product:** operating system for a single-tutor business

**Purpose:** test the Gauntlet accountability system while building useful software

This is the tutoring-platform application repository. It owns the React/TypeScript/
Bun/Vite frontend, FastAPI/SQLite backend, repository-local Playwright harness, and
product documentation.

Application code is separated into `frontend/`, `backend/`, and `e2e/`; root tooling
only orchestrates those boundaries.

The operational Gauntlet configuration and reusable accountability machinery remain
outside this repository in the Gauntlet ledger. This repository contains product code
and product decisions, but does not own grading or accountability-system behavior.

## Application function

The application supports the invite-only relationship between one Tutor and their
Students. Its current end-to-end flow is:

1. A Prospect views the public tutoring landing page.
2. The Tutor signs in with a passwordless magic link, creates a personalized
   Invitation, and keeps the Private Tutor Note separate from the Shared Personal
   Message shown to the Invitee.
3. The Invitee opens the opaque Invitation link, verifies the Invitation's bound email
   address, and completes the one-time Invitation Claim.
4. The resulting Student uses a server-side Student Session to submit a pending Session
   Request with a service, preferred time, timezone, and optional message.
5. The Tutor reviews pending Session Requests and can explicitly delete personal data
   collected during the pilot.

The Tutor can also correct, regenerate, or revoke an Invitation. A Session Request is
only a proposal: the current application does not confirm a Booking, take payment,
send production email, or synchronize a calendar. Those capabilities remain outside
the implemented pilot scope.

## Continue tomorrow

Continue with [`PRODUCT-GRILLING.md`](PRODUCT-GRILLING.md). It contains the settled
domain model, product policies, implementation constraints, and remaining product
questions from the grilling sessions.

Use [`CONTEXT.md`](CONTEXT.md) for canonical product language. [`GLOSSARY.md`](GLOSSARY.md)
remains as a compatibility pointer. Accountability terms remain in the external
Gauntlet ledger.

Do not silently turn unresolved questions into requirements. The adaptive planner may
schedule a product-decision task, freeze its answer, and then schedule implementation.

The frozen required slice is `landing page → personalized invitation → account claim
→ session request`. See [`BOUNDARIES.md`](BOUNDARIES.md). Grading uses only committed
and pushed repository evidence; deployment and external services are not required.
Every slice must also satisfy the security completion gate in
[`PRODUCT-GRILLING.md`](PRODUCT-GRILLING.md).

## Development

Prerequisites are Bun 1.3+, Python 3.12+, and `uv`.

```bash
bun run setup
bun run install:e2e
```

Run all current behavioral checks with:

```bash
bun run test
```

The end-to-end command builds the frontend, starts both application processes on local
test ports, creates and explicitly migrates an isolated SQLite database, runs
Playwright, and tears down the processes and temporary database. No pre-running
application services or persistent test state are used.

For local development, run the processes separately:

```bash
bun run dev:backend
bun run --cwd frontend dev --host 127.0.0.1 --port 7310
```

`dev:backend` applies Alembic migrations through root orchestration before starting
FastAPI. The API process never creates or upgrades its own schema. Test and production
environments must provide `TUTORING_DATABASE_URL`; development defaults to the ignored
`backend/var/tutoring.sqlite3` database.

The browser always calls relative `/api/*` paths. Vite proxies them to the local
FastAPI service, so the browser and API stay on one origin and the backend does not
enable CORS.

## Development page tour

Use two browser profiles for the complete tour: one normal window for the Tutor and
one private window for the Invitee/Student. The Tutor and Student use the same cookie
name, so keeping them separate prevents one role's session from replacing the other.

1. Start the backend and frontend with the commands above. If the development database
   does not have its single Tutor yet, run `bun run tutor:bootstrap tutor@example.com`.
2. Open `http://127.0.0.1:7310/` for the landing page, then open
   `http://127.0.0.1:7310/tutor/sign-in` and request a link for
   `tutor@example.com`.
3. Open `http://127.0.0.1:7310/api/development/outbox`, copy the newest
   `magic_link` into the Tutor window, and confirm sign-in. This reaches the Tutor
   workspace at `/tutor`.
4. Create an Invitation and inspect its Draft state. Activate it to inspect the Active
   state, then copy its one-time Invitation link.
5. Open the Invitation link in the private window to see the Invitee page. Request the
   verification link, return to the development outbox, and open its newest
   `magic_link` in that private window.
6. Confirm the Invitation Claim to reach `/student`. Submit the form to see the pending
   Session Request state, then refresh the Tutor workspace to see the request there.

The remaining states are action-driven rather than separate routes: regenerate or
revoke an active Invitation from the Tutor workspace, and select **Delete collected
data** on a pending request to see its guarded deletion state. For unavailable-state
checks, open `/invite/not-a-real-token`, or open `/student` in a fresh private window
without a Student Session. The development outbox does not exist in production.
