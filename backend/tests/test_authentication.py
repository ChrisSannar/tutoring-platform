import os
from pathlib import Path
import subprocess
import sys

from alembic import command
from alembic.config import Config


def test_repository_command_bootstraps_exactly_one_tutor(tmp_path: Path) -> None:
    database_url = f"sqlite:///{tmp_path / 'authentication.sqlite3'}"
    alembic_config = Config("backend/alembic.ini")
    alembic_config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(alembic_config, "head")
    environment = {
        **os.environ,
        "TUTORING_ENVIRONMENT": "test",
        "TUTORING_DATABASE_URL": database_url,
    }

    first = subprocess.run(
        [sys.executable, "-m", "app.bootstrap_tutor", "Tutor@Example.com"],
        cwd="backend",
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    second = subprocess.run(
        [sys.executable, "-m", "app.bootstrap_tutor", "other@example.com"],
        cwd="backend",
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    assert first.returncode == 0
    assert first.stdout.strip() == "Tutor created for tutor@example.com"
    assert second.returncode == 1
    assert second.stderr.strip() == "A Tutor already exists"
