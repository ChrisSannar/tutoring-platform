import argparse
from hashlib import sha256
import sys
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.authentication import issue_magic_link
from app.config import get_settings
from app.database import db_connection
from app.pilot_data import delete_student_pilot_data


def bootstrap(database_url: str, role: str, email: str) -> bool:
    try:
        with db_connection(database_url) as connection:
            if role == "tutor" and connection.execute(
                text("SELECT 1 FROM accounts WHERE role = 'tutor' LIMIT 1")
            ).first():
                return False
            connection.execute(
                text(
                    "INSERT INTO accounts (id, email, role, display_name) "
                    "VALUES (:id, :email, :role, :display_name)"
                ),
                {
                    "id": str(uuid4()),
                    "email": email,
                    "role": role,
                    "display_name": email if role == "student" else None,
                },
            )
    except IntegrityError:
        return False
    return True


def magic_link(database_url: str, role: str, email: str, ttl_seconds: int) -> str | None:
    with db_connection(database_url, mode="read") as connection:
        exists = connection.execute(
            text("SELECT 1 FROM accounts WHERE email = :email AND role = :role"),
            {"email": email, "role": role},
        ).first()
    return issue_magic_link(database_url, email, ttl_seconds) if exists else None


def remove(database_url: str, role: str, email: str) -> bool:
    with db_connection(database_url, mode="read") as connection:
        account_id = connection.execute(
            text("SELECT id FROM accounts WHERE email = :email AND role = :role"),
            {"email": email, "role": role},
        ).scalar_one_or_none()
    if account_id is None:
        return False
    if role == "student":
        return delete_student_pilot_data(database_url, account_id) is not None
    with db_connection(database_url) as connection:
        parameters = {"account_id": account_id}
        for table in ("login_requests", "authentication_sessions", "magic_link_tokens"):
            connection.execute(
                text(f"DELETE FROM {table} WHERE account_id = :account_id"),
                parameters,
            )
        connection.execute(
            text("DELETE FROM authentication_request_events WHERE email_hash = :hash"),
            {"hash": sha256(email.encode()).hexdigest()},
        )
        connection.execute(
            text("DELETE FROM accounts WHERE id = :account_id"), parameters
        )
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Manage pilot accounts")
    parser.add_argument("action", choices=("bootstrap", "magic-link", "remove"))
    parser.add_argument("role", choices=("tutor", "student"))
    parser.add_argument("email")
    arguments = parser.parse_args()
    email = arguments.email.strip().lower()
    settings = get_settings()
    label = arguments.role.title()

    if arguments.action == "bootstrap":
        if bootstrap(settings.database_url, arguments.role, email):
            print(f"{label} created for {email}")
            return 0
        message = f"A {label} already exists"
    elif arguments.action == "magic-link":
        token = magic_link(
            settings.database_url,
            arguments.role,
            email,
            settings.magic_link_ttl_seconds,
        )
        if token:
            print(f"/sign-in/confirm?token={token}")
            return 0
        message = f"{label} account is missing"
    elif remove(settings.database_url, arguments.role, email):
        print(f"{label} removed: {email}")
        return 0
    else:
        message = f"{label} account is missing"

    print(message, file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
