from datetime import datetime, timedelta, timezone
from hashlib import sha256
import secrets
from uuid import uuid4

from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError

from app.invitations.claim_sql import CLAIM_INVITATION, CREATE_ACCOUNT, CREATE_SESSION
from app.invitations.errors import InvitationClaimConflict


def claim_invitation(
    database_url: str,
    raw_claim_token: str,
    display_name: str,
    inactivity_seconds: int,
    absolute_seconds: int,
    previous_session: str | None,
) -> dict[str, str] | None:
    now = datetime.now(timezone.utc)
    account_id = str(uuid4())
    raw_session, raw_csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    token_hash = sha256(raw_claim_token.encode()).hexdigest()
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            claim = connection.execute(
                text(CLAIM_INVITATION),
                {
                    "display_name": display_name,
                    "account_id": account_id,
                    "token_hash": token_hash,
                    "now": now,
                },
            ).mappings().first()
            if claim is None:
                known_token = connection.execute(
                    text(
                        "SELECT 1 FROM invitation_claim_tokens "
                        "WHERE token_hash = :token_hash"
                    ),
                    {"token_hash": token_hash},
                ).first()
                if known_token is not None:
                    raise InvitationClaimConflict
                return None
            connection.execute(
                text(CREATE_ACCOUNT),
                {"id": account_id, "email": claim["email"], "display_name": display_name},
            )
            connection.execute(
                text(
                    "UPDATE invitation_claim_tokens SET consumed_at = :now "
                    "WHERE token_hash = :token_hash AND consumed_at IS NULL"
                ),
                {"now": now, "token_hash": token_hash},
            )
            if previous_session is not None:
                connection.execute(
                    text(
                        "UPDATE authentication_sessions SET revoked_at = :now "
                        "WHERE session_hash = :session_hash AND revoked_at IS NULL"
                    ),
                    {"now": now, "session_hash": sha256(previous_session.encode()).hexdigest()},
                )
            connection.execute(
                text(CREATE_SESSION),
                {
                    "id": str(uuid4()),
                    "account_id": account_id,
                    "session_hash": sha256(raw_session.encode()).hexdigest(),
                    "csrf_hash": sha256(raw_csrf.encode()).hexdigest(),
                    "inactive": now + timedelta(seconds=inactivity_seconds),
                    "absolute": now + timedelta(seconds=absolute_seconds),
                },
            )
            return {
                "status": "claimed",
                "role": "student",
                "email": claim["email"],
                "display_name": display_name,
                "session": raw_session,
                "csrf_token": raw_csrf,
            }
    except IntegrityError:
        raise InvitationClaimConflict from None
    finally:
        engine.dispose()
