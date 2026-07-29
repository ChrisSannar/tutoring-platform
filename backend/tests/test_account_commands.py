from hashlib import sha256
import os
import subprocess
import sys

import pytest

from app.authentication import consume_magic_link


def command(database_url: str, action: str, role: str, email: str):
    return subprocess.run(
        [sys.executable, "-m", "app.account_commands", action, role, email],
        cwd="backend",
        env={
            **os.environ,
            "TUTORING_ENVIRONMENT": "test",
            "TUTORING_DATABASE_URL": database_url,
        },
        check=False,
        capture_output=True,
        text=True,
    )


@pytest.mark.parametrize("role", ["tutor", "student"])
def test_account_commands_cover_account_lifecycle(testbed, role: str) -> None:
    database_url = testbed.database_url(f"{role}-commands")
    testbed.migrate(database_url)
    email = f"{role}@example.com"

    created = command(database_url, "bootstrap", role, f" {email.upper()} ")
    link = command(database_url, "magic-link", role, email)
    token = link.stdout.strip().partition("?token=")[2]
    consume_magic_link(database_url, token, 900, 1800, None)
    testbed.seed(
        database_url,
        (
            "INSERT INTO authentication_request_events "
            "(id, email_hash, ip_hash, requested_at) "
            "VALUES ('request', :email_hash, 'ip', CURRENT_TIMESTAMP)",
            {"email_hash": sha256(email.encode()).hexdigest()},
        ),
    )
    removed = command(database_url, "remove", role, email)

    assert created.returncode == 0
    assert created.stdout.strip() == f"{role.title()} created for {email}"
    assert link.returncode == 0
    assert link.stdout.startswith("/sign-in/confirm?token=")
    assert removed.returncode == 0
    assert removed.stdout.strip() == f"{role.title()} removed: {email}"
    assert testbed.fetch_one(database_url, "SELECT COUNT(*) FROM accounts") == 0
    assert testbed.fetch_one(
        database_url, "SELECT COUNT(*) FROM magic_link_tokens"
    ) == 0
    assert testbed.fetch_one(
        database_url, "SELECT COUNT(*) FROM authentication_sessions"
    ) == 0
    assert testbed.fetch_one(
        database_url, "SELECT COUNT(*) FROM authentication_request_events"
    ) == 0
