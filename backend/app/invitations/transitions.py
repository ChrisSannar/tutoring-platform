from datetime import datetime

from sqlalchemy import text
from sqlalchemy.engine import Connection

from app.invitations.expiration import expire_due_by_id, expire_due_by_token

ACTIVE_INVITATION_STATUSES = ("created", "opened")


def status_after_expiration(
    connection: Connection, invitation_id: str, now: datetime
) -> str | None:
    expire_due_by_id(connection, invitation_id, now)
    return connection.execute(
        text("SELECT status FROM invitations WHERE id = :id"), {"id": invitation_id}
    ).scalar()


def open_by_token(
    connection: Connection, token_hash: str, now: datetime
) -> dict[str, str] | None:
    expire_due_by_token(connection, token_hash, now)
    row = connection.execute(
        text(
            "UPDATE invitations SET status = 'opened', "
            "first_opened_at = COALESCE(first_opened_at, :now) "
            "WHERE token_hash = :token_hash AND status IN ('created', 'opened') "
            "AND expires_at > :now RETURNING email, display_name, shared_personal_message"
        ),
        {"token_hash": token_hash, "now": now},
    ).mappings().first()
    return dict(row) if row is not None else None


def claim_by_token(
    connection: Connection,
    token_hash: str,
    display_name: str,
    account_id: str,
    now: datetime,
):
    expire_due_by_token(connection, token_hash, now)
    return connection.execute(
        text(
            "UPDATE invitations SET status = 'claimed', display_name = :name, "
            "claimed_account_id = :account_id, claimed_at = :now, token_hash = NULL, "
            "token_ciphertext = NULL WHERE token_hash = :token_hash "
            "AND status IN ('created', 'opened') AND expires_at > :now "
            "RETURNING id, email, inquiry_id"
        ),
        {
            "name": display_name,
            "account_id": account_id,
            "token_hash": token_hash,
            "now": now,
        },
    ).mappings().first()


def revoke_by_id(connection: Connection, invitation_id: str, now: datetime) -> str | None:
    status = status_after_expiration(connection, invitation_id, now)
    if status == "revoked" or status is None:
        return status
    if status not in ACTIVE_INVITATION_STATUSES:
        return "conflict"
    return connection.execute(
        text(
            "UPDATE invitations SET status = 'revoked', revoked_at = :now, "
            "token_hash = NULL, token_ciphertext = NULL WHERE id = :id "
            "AND status IN ('created', 'opened') RETURNING status"
        ),
        {"id": invitation_id, "now": now},
    ).scalar()


def regenerate_by_id(
    connection: Connection, invitation_id: str, token_hash: str,
    ciphertext: bytes, created_at: datetime, expires_at: datetime,
) -> str | None:
    status = status_after_expiration(connection, invitation_id, created_at)
    if status is None:
        return None
    if status not in ACTIVE_INVITATION_STATUSES:
        return "conflict"
    return connection.execute(
        text(
            "UPDATE invitations SET status = 'created', token_hash = :token_hash, "
            "token_ciphertext = :ciphertext, created_at = :created_at, "
            "first_opened_at = NULL, expires_at = :expires_at WHERE id = :id "
            "AND status IN ('created', 'opened') RETURNING status"
        ),
        {"id": invitation_id, "token_hash": token_hash, "ciphertext": ciphertext,
         "created_at": created_at, "expires_at": expires_at},
    ).scalar()
