from pathlib import Path

from alembic import command
from alembic.config import Config
import httpx
import pytest

from app.config import get_settings
from app.main import create_app


@pytest.mark.anyio
async def test_explicitly_migrated_database_is_ready(
    monkeypatch, tmp_path: Path
) -> None:
    database_path = tmp_path / "ready.sqlite3"
    database_url = f"sqlite:///{database_path}"
    monkeypatch.setenv("TUTORING_ENVIRONMENT", "test")
    monkeypatch.setenv("TUTORING_DATABASE_URL", database_url)

    alembic_config = Config("backend/alembic.ini")
    alembic_config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(alembic_config, "head")

    get_settings.cache_clear()
    transport = httpx.ASGITransport(app=create_app())
    async with httpx.AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as client:
        response = await client.get("/api/ready")
    get_settings.cache_clear()

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


@pytest.mark.anyio
async def test_unmigrated_database_reports_sanitized_schema_failure(
    monkeypatch, tmp_path: Path
) -> None:
    database_path = tmp_path / "unmigrated.sqlite3"
    database_path.touch()
    monkeypatch.setenv("TUTORING_ENVIRONMENT", "test")
    monkeypatch.setenv("TUTORING_DATABASE_URL", f"sqlite:///{database_path}")

    get_settings.cache_clear()
    transport = httpx.ASGITransport(app=create_app())
    async with httpx.AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as client:
        response = await client.get("/api/ready")
    get_settings.cache_clear()

    assert response.status_code == 503
    assert response.json() == {"status": "not_ready", "reason": "schema"}


@pytest.mark.anyio
async def test_inaccessible_database_reports_sanitized_database_failure(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("TUTORING_ENVIRONMENT", "test")
    monkeypatch.setenv("TUTORING_DATABASE_URL", f"sqlite:///{tmp_path}")

    get_settings.cache_clear()
    transport = httpx.ASGITransport(app=create_app())
    async with httpx.AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as client:
        response = await client.get("/api/ready")
    get_settings.cache_clear()

    assert response.status_code == 503
    assert response.json() == {"status": "not_ready", "reason": "database"}
    assert str(tmp_path) not in response.text
