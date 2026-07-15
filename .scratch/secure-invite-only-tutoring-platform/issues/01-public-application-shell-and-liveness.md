# 01 — Public Application Shell and Liveness

**What to build:** A clean checkout can start the public React application and FastAPI service through the repository Playwright command, show the Tutor's landing page, and report sanitized liveness.

**Blocked by:** None — can start immediately.

**Status:** ready-for-agent

- [ ] Locked Bun and Python dependencies install reproducibly through root orchestration.
- [ ] The public landing page renders and calls only same-origin relative API paths.
- [ ] `GET /api/health` returns only HTTP 200 with `{"status":"ok"}`.
- [ ] Baseline configuration, safe errors/logging, and browser security headers satisfy the security gate.
- [ ] A red-first Playwright test proves one command owns both processes without pre-running services.
