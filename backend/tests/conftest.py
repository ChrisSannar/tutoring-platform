import pytest


@pytest.fixture(autouse=True)
def test_invitation_encryption_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "TUTORING_INVITATION_ENCRYPTION_KEY",
        "a2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2s=",
    )


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"
