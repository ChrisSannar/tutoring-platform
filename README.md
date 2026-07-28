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
bun run tutor:bootstrap -- tutor@example.com
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
