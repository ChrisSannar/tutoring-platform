import sys

from sqlalchemy import create_engine, text

from app.authentication import issue_magic_link
from app.config import get_settings


def main() -> int:
    settings = get_settings()
    engine = create_engine(settings.database_url)
    try:
        with engine.connect() as connection:
            row = connection.execute(
                text("SELECT email FROM accounts WHERE role = 'tutor' LIMIT 1")
            ).mappings().first()
    finally:
        engine.dispose()
    if row is None:
        print("Tutor account is missing", file=sys.stderr)
        return 1
    token = issue_magic_link(
        settings.database_url, row["email"], settings.magic_link_ttl_seconds
    )
    if token is None:
        print("Tutor Login Link could not be generated", file=sys.stderr)
        return 1
    print(f"/sign-in/confirm?token={token}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
