import os
from pathlib import Path
import subprocess
import sys
from urllib.parse import parse_qs, urlparse

from alembic import command
from alembic.config import Config
import httpx
import pytest
from sqlalchemy import create_engine, text

from app.authentication import issue_magic_link
from app.config import get_settings
from app.main import create_app

TEST_ORIGIN = "http://testserver"


@pytest.fixture(autouse=True)
def test_invitation_encryption_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "TUTORING_INVITATION_ENCRYPTION_KEY",
        "a2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2s=",
    )


@pytest.fixture(autouse=True)
def fresh_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


class Testbed:
    """Owns per-test environment, migrated tmp database, and client plumbing."""

    def __init__(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        self._monkeypatch = monkeypatch
        self.tmp_path = tmp_path

    def database_url(self, name: str = "test") -> str:
        return f"sqlite:///{self.tmp_path / f'{name}.sqlite3'}"

    def setenv(self, database_url: str, origin: str | None = TEST_ORIGIN) -> None:
        self._monkeypatch.setenv("TUTORING_ENVIRONMENT", "test")
        self._monkeypatch.setenv("TUTORING_DATABASE_URL", database_url)
        if origin is not None:
            self._monkeypatch.setenv("TUTORING_APPLICATION_ORIGIN", origin)

    def migrated(self, name: str = "test", *, origin: str | None = TEST_ORIGIN) -> str:
        database_url = self.database_url(name)
        self.migrate(database_url)
        self.setenv(database_url, origin)
        return database_url

    @staticmethod
    def migrate(database_url: str, revision: str = "head") -> None:
        config = Config("backend/alembic.ini")
        config.set_main_option("sqlalchemy.url", database_url)
        command.upgrade(config, revision)

    @staticmethod
    def seed(database_url: str, *statements: str | tuple[str, dict]) -> None:
        engine = create_engine(database_url)
        with engine.begin() as connection:
            for statement in statements:
                sql, params = (statement, {}) if isinstance(statement, str) else statement
                connection.execute(text(sql), params)
        engine.dispose()

    @staticmethod
    def fetch_all(database_url: str, sql: str) -> list:
        engine = create_engine(database_url)
        with engine.connect() as connection:
            rows = connection.execute(text(sql)).all()
        engine.dispose()
        return rows

    @staticmethod
    def fetch_one(database_url: str, sql: str):
        engine = create_engine(database_url)
        with engine.connect() as connection:
            value = connection.execute(text(sql)).scalar_one()
        engine.dispose()
        return value

    def app(self, now=None):
        application = create_app()
        if now is not None:
            application.state.context.now = now
        return application

    def client(self, app=None, *, now=None, headers=None) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app if app is not None else self.app(now)),
            base_url=TEST_ORIGIN,
            headers=headers,
        )

    async def sign_in(
        self, client: httpx.AsyncClient, database_url: str, email: str
    ) -> str:
        token = issue_magic_link(database_url, email, 900)
        confirmed = await client.post(
            "/api/auth/magic-links/confirm", json={"token": token}
        )
        return confirmed.json()["csrf_token"]

    async def authenticate(self, transport, database_url: str, email: str):
        client = httpx.AsyncClient(transport=transport, base_url=TEST_ORIGIN)
        return client, await self.sign_in(client, database_url, email)

    async def outbox_sign_in(
        self, client: httpx.AsyncClient, email: str = "tutor@example.com"
    ) -> str:
        await client.post("/api/auth/magic-links", json={"email": email})
        outbox = await client.get("/api/development/outbox")
        token = parse_qs(
            urlparse(outbox.json()["messages"][-1]["magic_link"]).query
        )["token"][0]
        confirmed = await client.post(
            "/api/auth/magic-links/confirm", json={"token": token}
        )
        return confirmed.json()["csrf_token"]

    def bootstrap_tutor(
        self, database_url: str, email: str = "tutor@example.com", *, check: bool = True
    ):
        return subprocess.run(
            [sys.executable, "-m", "app.bootstrap_tutor", email],
            cwd="backend",
            env={
                **os.environ,
                "TUTORING_ENVIRONMENT": "test",
                "TUTORING_DATABASE_URL": database_url,
            },
            check=check,
            capture_output=True,
            text=True,
        )


@pytest.fixture
def testbed(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Testbed:
    return Testbed(monkeypatch, tmp_path)
