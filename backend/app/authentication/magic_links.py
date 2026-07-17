from datetime import datetime, timedelta, timezone
from hashlib import sha256
import secrets
from uuid import uuid4

from sqlalchemy import create_engine, text

def issue_magic_link(database_url: str, email: str, ttl_seconds: int) -> str | None:
    normalized_email = email.strip().lower()
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            account = connection.execute(
                text("SELECT id FROM accounts WHERE email = :email"),
                {"email": normalized_email},
            ).mappings().first()
            if account is None:
                return None
            raw_token = secrets.token_urlsafe(32)
            connection.execute(
                text(
                    "INSERT INTO magic_link_tokens "
                    "(id, account_id, token_hash, expires_at, consumed_at) "
                    "VALUES (:id, :account_id, :token_hash, :expires_at, NULL)"
                ),
                {
                    "id": str(uuid4()),
                    "account_id": account["id"],
                    "token_hash": sha256(raw_token.encode()).hexdigest(),
                    "expires_at": datetime.now(timezone.utc)
                    + timedelta(seconds=ttl_seconds),
                },
            )
            return raw_token
    finally:
        engine.dispose()

def magic_link_is_active(database_url: str, raw_token: str) -> bool:
    engine = create_engine(database_url)
    try:
        with engine.connect() as connection:
            token = connection.execute(
                text(
                    "SELECT 1 FROM magic_link_tokens WHERE token_hash = :token_hash "
                    "AND consumed_at IS NULL AND expires_at > :now"
                ),
                {
                    "token_hash": sha256(raw_token.encode()).hexdigest(),
                    "now": datetime.now(timezone.utc),
                },
            ).first()
            return token is not None
    finally:
        engine.dispose()
