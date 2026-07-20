from datetime import datetime, timezone
from hashlib import sha256

from sqlalchemy import create_engine

from app.invitations.transitions import open_by_token

def get_active_invitation_by_token(
    database_url: str, raw_token: str
) -> dict[str, str] | None:
    token_hash = sha256(raw_token.encode()).hexdigest()
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            return open_by_token(
                connection, token_hash, datetime.now(timezone.utc)
            )
    finally:
        engine.dispose()
