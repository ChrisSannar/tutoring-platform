import pytest


@pytest.mark.anyio
async def test_explicitly_migrated_database_is_ready(testbed) -> None:
    database_url = testbed.database_url("ready")
    testbed.setenv(database_url, origin=None)
    testbed.migrate(database_url)

    response = await testbed.client().get("/api/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


@pytest.mark.anyio
async def test_unmigrated_database_reports_sanitized_schema_failure(testbed) -> None:
    database_path = testbed.tmp_path / "unmigrated.sqlite3"
    database_path.touch()
    testbed.setenv(f"sqlite:///{database_path}", origin=None)

    response = await testbed.client().get("/api/ready")

    assert response.status_code == 503
    assert response.json() == {"status": "not_ready", "reason": "schema"}


@pytest.mark.anyio
async def test_inaccessible_database_reports_sanitized_database_failure(testbed) -> None:
    testbed.setenv(f"sqlite:///{testbed.tmp_path}", origin=None)

    response = await testbed.client().get("/api/ready")

    assert response.status_code == 503
    assert response.json() == {"status": "not_ready", "reason": "database"}
    assert str(testbed.tmp_path) not in response.text
