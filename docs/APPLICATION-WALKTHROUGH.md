# Application Walkthrough

The application is a thin, invite-only tutoring workflow:

`Landing page -> Tutor sign-in -> Invitation -> Invitee verification -> Invitation Claim -> Student Session Request -> Tutor review/deletion`

The current running code still uses `draft -> active`. The July 16 product grilling
established the intended replacement, `created -> opened`, but that change has not yet
been implemented.

## 1. Run the application

Prerequisites are Bun 1.3+, Python 3.12+, and `uv`.

Run the one-time setup:

```bash
bun run setup
bun run install:e2e
bun run migrate:dev
bun run tutor:bootstrap -- tutor@example.com
```

- `setup` installs locked frontend and Python dependencies.
- `install:e2e` installs Playwright Chromium.
- `migrate:dev` creates `backend/var/` and applies every Alembic migration.
- `tutor:bootstrap` runs `backend/app/bootstrap_tutor.py` and creates the one allowed
  Tutor account.

Start the backend in terminal one:

```bash
bun run serve:backend
```

Start the frontend in terminal two:

```bash
bun run serve:frontend
```

Then visit:

```text
http://127.0.0.1:7310/
```

Use `serve:frontend` for now. The documented Vite `dev` server applies a production
Content Security Policy that blocks its own React Refresh preamble; the production
build/preview path avoids that existing defect.

Use separate browser profiles for the Tutor and Student. Both roles use the same
cookie name, so signing in as one role in the same profile replaces the other role's
session.

## 2. Application startup

The frontend build starts at `frontend/src/main.tsx`, mounts React, and renders
`frontend/src/app/Application.tsx`.

There is no routing library. `Application` reads `window.location.pathname` and chooses:

| URL | Component |
| --- | --- |
| `/` | `LandingPage` |
| `/tutor/*` | `TutorAuthentication` |
| `/invite/:token` | `InviteeSetup` |
| `/student/claim/confirm` | `InvitationClaimConfirmation` |
| `/student` | `StudentWorkspace` |

The backend starts `backend/app/main.py`, creates one FastAPI application, disables
public OpenAPI documentation, installs sanitized error handling, and registers all API
routers.

Vite proxies relative `/api/*` requests from port 7310 to FastAPI on port 7311. There
is no CORS boundary.

## 3. Landing page

Open:

```text
http://127.0.0.1:7310/
```

Execution path:

1. Vite serves `index.html` and the compiled JavaScript.
2. `frontend/src/main.tsx` renders `Application`.
3. No specialized path matches, so `Application` renders
   `frontend/src/landing/LandingPage.tsx`.
4. The page shows the tutoring proposition and a `mailto:tutor@example.com` contact
   link.

There is currently no public signup, service catalog, price display, or public
scheduling flow.

Infrastructure endpoints:

- `GET /api/health` returns `{"status":"ok"}`.
- `GET /api/ready` checks database access and the Alembic revision.

Those routes live in `backend/app/routes/system.py`. Readiness logic is in
`backend/app/database.py`. Browser security headers are configured in
`frontend/vite.config.ts`.

## 4. Tutor passwordless sign-in

Open:

```text
http://127.0.0.1:7310/tutor/sign-in
```

Frontend path:

1. `Application` renders `frontend/src/tutor/TutorAuthentication.tsx`.
2. Enter `tutor@example.com`.
3. The form sends `POST /api/auth/magic-links`.
4. The page changes to **Check the development outbox**.

Backend path:

1. `backend/app/routes/auth_magic_links.py` normalizes the email.
2. Requests are rate-limited by hashed email and IP.
3. `backend/app/authentication/magic_links.py` checks that the account exists.
4. It generates a 32-byte URL-safe token.
5. Only its SHA-256 hash and 15-minute expiry are stored.
6. Development adds the raw link to an in-memory outbox.

Inspect the outbox at:

```text
http://127.0.0.1:7310/api/development/outbox
```

Take the newest relative `magic_link` and append it to the frontend origin, for example:

```text
http://127.0.0.1:7310/tutor/sign-in/confirm?token=...
```

Click **Confirm sign-in**. The frontend sends
`POST /api/auth/magic-links/confirm`.

`backend/app/authentication/session_creation.py` then:

- atomically consumes the magic-link token;
- revokes the previous browser session, if present;
- generates session and CSRF tokens;
- stores only their hashes; and
- sets the session inactivity and absolute deadlines.

The browser receives an HTTP-only session cookie, a readable CSRF cookie, and the raw
CSRF value in the response. It then reaches the Tutor workspace.

## 5. Tutor workspace

`frontend/src/tutor/TutorWorkspace.tsx` contains:

- pending Session Requests;
- the Invitation manager; and
- logout.

Opening `/tutor` directly first calls `GET /api/tutor/session`. Unauthorized visitors
return to the sign-in screen.

Every Tutor mutation requires:

- an active Tutor session;
- the corresponding CSRF token; and
- the exact configured same-origin `Origin`.

That enforcement is centralized in `backend/app/http/security.py`.

## 6. Creating an Invitation

The form is `frontend/src/tutor/InvitationManager.tsx`. It collects:

- Invitee email;
- display name;
- Shared Personal Message; and
- Private Tutor Note.

Clicking **Create Invitation** sends:

```http
POST /api/tutor/invitations
```

The route is in `backend/app/routes/tutor_invitation_records.py`. The current
implementation calls `backend/app/invitations/records.py`, which:

- normalizes the email;
- stores shared and private content in separate columns;
- creates status `draft`; and
- creates no token yet.

The Tutor sees **Draft Invitation for Avery**.

### Activation

Click **Activate Invitation**. That sends:

```http
POST /api/tutor/invitations/:id/activate
```

`backend/app/invitations/activation.py`:

- requires current state `draft`;
- generates a URL-safe token;
- stores only its SHA-256 hash;
- sets a seven-day expiration;
- changes status to `active`; and
- returns `/invite/<raw-token>` once.

This two-step behavior is what the paused grilling intends to replace with immediate
token issuance and `created -> opened`.

### Other current Invitation controls

The Tutor can also:

- correct the bound email while `draft` or `active`;
- regenerate the token on the same active record; and
- revoke an active Invitation.

Those endpoints are in `backend/app/routes/tutor_invitation_lifecycle.py`.

Current behavior differs from the new decisions:

- regeneration reuses the same Invitation row;
- revocation is not idempotent; and
- there is no `opened` status or lifecycle timestamp set.

## 7. Invitee setup page

Open the Invitation link in a private browser window:

```text
http://127.0.0.1:7310/invite/<token>
```

`frontend/src/invitations/InviteeSetup.tsx` extracts the token and requests:

```http
GET /api/invitations/:token
```

`backend/app/invitations/tokens.py`:

- hashes the supplied token;
- marks an expired active Invitation `expired`;
- accepts only an unexpired `active` record; and
- selects only email, display name, and Shared Personal Message.

The response model also allowlists only those three fields. The Private Tutor Note is
neither selected nor serialized.

Invalid, revoked, expired, regenerated, and claimed tokens receive the same sanitized
`404` response.

Current missing behavior: a successful open does not persist `opened` or
`first_opened_at`.

## 8. Invitee email verification

On the setup page, click **Email verification link**.

The frontend sends:

```http
POST /api/invitations/:invitation-token/magic-links
```

`backend/app/invitations/claim_tokens.py`:

- verifies the Invitation token;
- requires the submitted normalized email to match the bound email;
- creates a separate one-use claim token;
- stores only its hash; and
- gives it a 15-minute deadline.

The HTTP response is always generic, whether or not the email matched.

Open the newest development-outbox link in the private window:

```text
http://127.0.0.1:7310/student/claim/confirm?token=...
```

## 9. Claiming the Invitation

`frontend/src/invitations/InvitationClaimConfirmation.tsx` first sends a safe GET to
inspect the claim token. This does not consume it.

The page shows:

- immutable bound email;
- editable display name; and
- a confirmation button.

Clicking **Confirm Invitation Claim** sends:

```http
POST /api/invitation-claims/confirm
```

`backend/app/invitations/claiming.py` performs one transaction that:

- changes the Invitation from `active` to `claimed`;
- associates it with a new Student account;
- clears the Invitation token hash;
- consumes the claim token;
- revokes any previous browser session; and
- creates the Student authentication session.

Concurrent claims are designed to produce one winner and one `409` conflict.

## 10. Student workspace and Session Request

After claiming, the browser reaches:

```text
http://127.0.0.1:7310/student
```

`frontend/src/students/StudentWorkspace.tsx` restores the Student with:

```http
GET /api/student/session
```

The Session Request form supports:

- Algebra or Geometry tutoring;
- preferred local date/time;
- IANA timezone; and
- an optional message up to 1,000 characters.

Submission sends:

```http
POST /api/student/session-requests
X-CSRF-Token: ...
Idempotency-Key: <browser-generated UUID>
```

`backend/app/session_requests/commands.py`:

- identifies the Student from the session;
- returns the existing request if that Student already used the idempotency key;
- converts the preferred instant to UTC; and
- persists status `pending`.

It is deliberately a proposal, not a confirmed Booking.

## 11. Tutor reviews requests

On the Tutor workspace, `frontend/src/tutor/PendingSessionRequests.tsx` calls:

```http
GET /api/tutor/session-requests
```

`backend/app/session_requests/queries.py` joins requests to Student accounts and returns:

- Student name and email;
- requested service;
- preferred time and timezone;
- optional message; and
- `pending` status.

There is no accept, decline, scheduling, payment, or calendar workflow yet.

## 12. Pilot-data deletion

Beside a Student's request, the Tutor can choose **Delete collected data**.

The interface requires the exact phrase:

```text
DELETE COLLECTED DATA
```

It then calls:

```http
DELETE /api/tutor/students/:studentAccountId/pilot-data
```

`backend/app/pilot_data.py` transactionally removes:

- Invitation Claim tokens;
- claimed Invitations;
- Session Requests;
- authentication sessions;
- magic-link tokens;
- authentication rate-limit records for the Student email; and
- the Student account.

The Tutor account remains. Existing Student cookies become unusable.

## 13. Persistence

Alembic migrations create:

1. Accounts, authentication tokens, sessions, and rate-limit events.
2. Invitations with separate shared/private columns.
3. Invitation Claim tokens.
4. Student display names and claimed-account association.
5. Session Requests and per-Student idempotency uniqueness.

The migration chain begins in
`backend/migrations/versions/20260715_0001_initial_schema.py`.

Development data lives at:

```text
backend/var/tutoring.sqlite3
```

The API never migrates the database itself; orchestration does that before startup.

## 14. Tests and present status

Run:

```bash
bun run test
```

This executes backend tests followed by Playwright.

Verification while preparing this walkthrough:

- Backend: **63 passed**.
- Browser suite: could not start because port `7311` was already occupied in the
  execution environment. Playwright intentionally refuses to reuse existing servers.

Before running E2E locally, stop anything using ports 7310 and 7311, then run:

```bash
bun run test:e2e
```

Existing browser coverage includes:

- landing page and security headers;
- Tutor sign-in/logout;
- Invitation creation, activation, correction, regeneration, and revocation UI;
- Invitee-visible message without Private Tutor Note;
- Invitation Claim;
- Student Session Request and Tutor visibility; and
- guarded pilot-data deletion.

For the July 16 requirements, the important E2E gaps are:

- invalid Invitation token rejection;
- proving a revoked token no longer loads; and
- the new `created -> opened` lifecycle.

The current revocation E2E test checks only that the Tutor UI says **Revoked**; it does
not reopen the old Invitee link.

## 15. Features not implemented

The current application does not yet provide:

- production email delivery;
- public registration;
- a public service catalog or pricing;
- confirmed Bookings;
- accepting or declining Session Requests;
- payment;
- calendar synchronization;
- reminders;
- lesson-note management; or
- file/resource sharing.

These remain outside the implemented pilot slice.
