# 01 — Public Application Shell and Liveness

**What to build:** A clean checkout can start the public React application and FastAPI service through the repository Playwright command, show the Tutor's landing page, and report sanitized liveness.

**Blocked by:** None — can start immediately.

**Status:** resolved

- [x] Locked Bun and Python dependencies install reproducibly through root orchestration.
- [x] The public landing page renders and calls only same-origin relative API paths.
- [x] `GET /api/health` returns only HTTP 200 with `{"status":"ok"}`.
- [x] Baseline configuration, safe errors/logging, and browser security headers satisfy the security gate.
- [x] A red-first Playwright test proves one command owns both processes without pre-running services.

## Comments

- Implemented as red-green slices at the confirmed Playwright and black-box HTTP seams.
- Verified `bun run setup`, `bun run build`, and `bun run test` from the repository root.
- Playwright owns the production frontend build, FastAPI process, browser execution, and teardown with `reuseExistingServer: false`.
