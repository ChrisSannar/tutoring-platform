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
