# Use synchronous SQLAlchemy with Alembic

The FastAPI backend uses synchronous SQLAlchemy 2.x for SQLite access and Alembic as
the sole schema authority. This avoids the operational complexity of asynchronous
SQLite and a custom migration system while providing explicit, testable schema
revisions for startup tooling and `GET /api/ready`. The FastAPI process does not apply
migrations during startup; repository orchestration applies them explicitly before
launch, and an outdated schema leaves the process alive but not ready.
