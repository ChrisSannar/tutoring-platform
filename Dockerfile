# syntax=docker/dockerfile:1

FROM oven/bun:1.3.9 AS frontend
WORKDIR /app
COPY package.json bun.lock ./
COPY frontend/package.json frontend/package.json
RUN bun install --frozen-lockfile
COPY frontend frontend
RUN bun run build

FROM python:3.12-slim-bookworm AS backend
COPY --from=ghcr.io/astral-sh/uv:0.12.0 /uv /uvx /bin/
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
WORKDIR /app/backend
COPY backend/pyproject.toml backend/uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project

FROM python:3.12-slim-bookworm
ENV PATH="/app/backend/.venv/bin:$PATH" \
    PYTHONPATH="/app/backend" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app
RUN useradd --create-home --uid 10001 app \
    && mkdir /data \
    && chown app:app /data
COPY --from=backend /app/backend/.venv backend/.venv
COPY backend/app backend/app
COPY backend/migrations backend/migrations
COPY backend/alembic.ini backend/alembic.ini
COPY --from=frontend /app/frontend/dist frontend/dist
USER 10001:10001
EXPOSE 7310
CMD ["sh", "-c", "alembic -c backend/alembic.ini upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port 7310 --no-access-log"]
