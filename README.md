# Tutoring Platform

An invite-only operating system for one Tutor and their Students. The application owns
public Inquiry intake, personal Invitations, passwordless access, direct Booking,
availability, Session Credits, and Shared Lesson Notes.

Direct Booking is the sole scheduling model. Historical Session Request migrations and
decision records remain only to explain the explicit disposable-pilot schema transition;
no Session Request is converted into a Booking.

## Run locally

Prerequisites: Bun 1.3+, Python 3.12+, and `uv`.

```bash
bun run setup
bun run install:e2e
bun run migrate:dev
UV_CACHE_DIR=/tmp/tutoring-platform-uv-cache uv run --project backend python -m app.account_commands bootstrap tutor tutor@example.com
```

Start the backend and frontend in separate terminals:

```bash
bun run dev:backend
bun run --cwd frontend dev --host 127.0.0.1 --port 7310
```

Open `http://127.0.0.1:7310/`. Use separate browser profiles for Tutor and Student
sessions because both roles deliberately share one session-cookie name.

## Verify

```bash
bun run test
```

The root command runs black-box FastAPI tests, builds the frontend, migrates a fresh
temporary SQLite database, starts both application processes on randomized localhost
ports, runs Playwright, and removes all temporary state. It requires no mail,
calendar-provider, or other external network service.

## Product journey

1. A Prospect submits an Inquiry from the public landing page.
2. The Tutor creates and manually sends an encrypted, redisplayable Invitation Link.
3. Opening the link is observational; selecting **Create Account** atomically claims it,
   creates the Student Session, and grants one Session Credit.
4. The Student selects a derived Bookable Slot and redeems one Session Credit. When the
   Booking becomes Past, the credit is restored exactly once.
5. The Tutor operates Bookings, Students, Inquiries, Login Requests, and Lesson
   Note Drafts. Only explicit publication shares a note with the Student.

See [CONTEXT.md](CONTEXT.md) for canonical domain language,
[docs/APPLICATION-WALKTHROUGH.md](docs/APPLICATION-WALKTHROUGH.md) for the code tour, and
[docs/adr/](docs/adr/) for architectural decisions.

## Deploy

The production image is one Linux AMD64 container. It runs Alembic before Uvicorn,
serves the built frontend and API on one origin, and stores the pilot SQLite database
in a named Docker volume. HTTPS remains the responsibility of the host reverse proxy.

### Publish

Create a GitHub personal access token (classic) with `write:packages`, then authenticate
the publisher:

```bash
export CR_PAT=your-token
echo "$CR_PAT" | docker login ghcr.io -u chrissannar --password-stdin
make publish
```

The first publish creates `ghcr.io/chrissannar/tutoring-platform` and pushes both
`latest` and the full Git commit SHA. In the package settings on GitHub, change the
package visibility to **Public** so the server can pull without registry credentials.

### First launch

The server needs Linux AMD64, Docker Engine with the Compose plugin, Make, OpenSSL, and
outbound access to GHCR. Clone this repository only for its Compose and Make files:

```bash
cp .env.example .env
openssl rand -base64 32 | tr '+/' '-_'
```

Put the generated key in `.env`, set `TUTORING_APPLICATION_ORIGIN` to the public HTTPS
origin with no trailing slash, then launch:

```bash
make up
make status
make tutor-bootstrap EMAIL=tutor@example.com
make tutor-magic-link EMAIL=tutor@example.com
```

The magic-link command prints a relative Login Link. Append it to
`TUTORING_APPLICATION_ORIGIN` and deliver it privately. Opening the link still requires
the Tutor to select its confirmation action.

### Pilot accounts

These commands operate on the database inside the running container:

```bash
make tutor-bootstrap EMAIL=tutor@example.com
make student-bootstrap EMAIL=student@example.com
make tutor-magic-link EMAIL=tutor@example.com
make student-magic-link EMAIL=student@example.com
make remove-tutor EMAIL=tutor@example.com CONFIRM=remove-tutor
make remove-student EMAIL=student@example.com CONFIRM=remove-student
```

Bootstrap commands create accounts directly; Student bootstrap does not create an
Invitation or Session Credit. Magic-link commands print relative links. Removal clears
the selected account's authentication records; Student removal also clears that
Student's Invitations, Bookings, Session Credits, and Shared Lesson Notes.

Configure the existing HTTPS reverse proxy to forward the public origin to
`http://127.0.0.1:7310`, preserving the request host. The container port is deliberately
unavailable on non-loopback host interfaces. Set `TUTORING_PORT` in the shell when a
different loopback port is required.

### Operate

Pull and recreate the app on a newer `latest` image:

```bash
make up
```

Roll back to an immutable published commit:

```bash
TUTORING_IMAGE=ghcr.io/chrissannar/tutoring-platform:FULL_COMMIT_SHA make up
```

Inspect or stop the service:

```bash
make logs
make status
make down
```

`make down` keeps the SQLite volume. This disposable pilot deployment does not include
database backup or restore automation.
