import argparse
import sys
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.config import get_settings
from app.database import db_connection


def main() -> int:
    parser = argparse.ArgumentParser(description="Create the single Tutor account")
    parser.add_argument("email")
    arguments = parser.parse_args()
    normalized_email = arguments.email.strip().lower()
    try:
        with db_connection(get_settings().database_url) as connection:
            existing_tutor = connection.execute(
                text("SELECT 1 FROM accounts WHERE role = 'tutor' LIMIT 1")
            ).first()
            if existing_tutor is not None:
                print("A Tutor already exists", file=sys.stderr)
                return 1
            connection.execute(
                text(
                    "INSERT INTO accounts (id, email, role) "
                    "VALUES (:id, :email, 'tutor')"
                ),
                {"id": str(uuid4()), "email": normalized_email},
            )
    except IntegrityError:
        print("A Tutor already exists", file=sys.stderr)
        return 1

    print(f"Tutor created for {normalized_email}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
