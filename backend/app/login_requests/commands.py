from datetime import datetime, timedelta, timezone
from hashlib import sha256
import secrets
from uuid import uuid4

from sqlalchemy import create_engine, text


def queue_student_login_request(database_url: str, email: str) -> bool:
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            account = connection.execute(
                text("SELECT id, role FROM accounts WHERE email = :email"),
                {"email": email},
            ).mappings().first()
            if account is None or account["role"] != "student":
                return False
            active = connection.execute(
                text(
                    "SELECT 1 FROM login_requests LEFT JOIN magic_link_tokens ON "
                    "magic_link_tokens.id = magic_link_token_id WHERE "
                    "login_requests.account_id = :id "
                    "AND dismissed_at IS NULL AND (magic_link_token_id IS NULL OR "
                    "(consumed_at IS NULL AND expires_at > :now))"
                ),
                {"id": account["id"], "now": datetime.now(timezone.utc)},
            ).first()
            if active is None:
                connection.execute(
                    text(
                        "INSERT INTO login_requests (id, account_id, requested_at) "
                        "VALUES (:id, :account_id, :requested_at)"
                    ),
                    {"id": str(uuid4()), "account_id": account["id"], "requested_at": datetime.now(timezone.utc)},
                )
            return True
    finally:
        engine.dispose()


def generate_login_link(database_url: str, request_id: str, ttl_seconds: int) -> str | None:
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            request = connection.execute(
                text(
                    "SELECT account_id FROM login_requests WHERE id = :id "
                    "AND dismissed_at IS NULL AND magic_link_token_id IS NULL"
                ),
                {"id": request_id},
            ).mappings().first()
            if request is None:
                return None
            token_id, raw_token = str(uuid4()), secrets.token_urlsafe(32)
            connection.execute(
                text(
                    "INSERT INTO magic_link_tokens (id, account_id, token_hash, "
                    "expires_at, consumed_at) VALUES (:id, :account_id, :hash, :expires, NULL)"
                ),
                {"id": token_id, "account_id": request["account_id"], "hash": sha256(raw_token.encode()).hexdigest(), "expires": datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)},
            )
            connection.execute(
                text("UPDATE login_requests SET magic_link_token_id = :token_id WHERE id = :id"),
                {"token_id": token_id, "id": request_id},
            )
            return raw_token
    finally:
        engine.dispose()


def dismiss_login_request(database_url: str, request_id: str) -> bool:
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            now = datetime.now(timezone.utc)
            connection.execute(
                text(
                    "UPDATE magic_link_tokens SET consumed_at = :now WHERE id = "
                    "(SELECT magic_link_token_id FROM login_requests WHERE id = :id) "
                    "AND consumed_at IS NULL"
                ),
                {"id": request_id, "now": now},
            )
            result = connection.execute(
                text("UPDATE login_requests SET dismissed_at = :now WHERE id = :id AND dismissed_at IS NULL"),
                {"id": request_id, "now": now},
            )
            return result.rowcount == 1
    finally:
        engine.dispose()
