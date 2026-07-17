import pytest
from pydantic import ValidationError

from app.config import Settings


def test_non_development_requires_an_explicit_database_url(monkeypatch) -> None:
    monkeypatch.delenv("TUTORING_DATABASE_URL", raising=False)

    with pytest.raises(ValidationError):
        Settings(environment="production", _env_file=None)


def test_frontend_served_database_path_is_rejected(monkeypatch) -> None:
    monkeypatch.delenv("TUTORING_DATABASE_URL", raising=False)

    with pytest.raises(ValidationError):
        Settings(
            environment="test",
            database_url="sqlite:///frontend/public/pilot.sqlite3",
            _env_file=None,
        )


def test_non_development_requires_a_valid_invitation_encryption_key(
    monkeypatch,
) -> None:
    monkeypatch.delenv("TUTORING_INVITATION_ENCRYPTION_KEY", raising=False)

    with pytest.raises(ValidationError):
        Settings(
            environment="production",
            database_url="sqlite:///:memory:",
            _env_file=None,
        )

    with pytest.raises(ValidationError):
        Settings(
            environment="production",
            database_url="sqlite:///:memory:",
            invitation_encryption_key="not-a-valid-key",
            _env_file=None,
        )
