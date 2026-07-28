from datetime import datetime, timedelta, timezone
from hashlib import sha256
import secrets
from uuid import uuid4

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import text
from sqlalchemy.engine import Connection
from sqlalchemy.exc import IntegrityError

from app.database import db_connection


class InvitationClaimConflict(Exception):
    pass


def encrypt_invitation_token(raw_token: str, encryption_key: str) -> bytes:
    return Fernet(encryption_key.encode()).encrypt(raw_token.encode())


def decrypt_invitation_token(
    token_ciphertext: bytes, encryption_key: str
) -> str | None:
    try:
        return Fernet(encryption_key.encode()).decrypt(token_ciphertext).decode()
    except InvalidToken:
        return None


def expire_due_by_id(
    connection: Connection, invitation_id: str, now: datetime
) -> None:
    connection.execute(
        text(
            "UPDATE invitations SET status = 'expired', expired_at = :now, "
            "token_hash = NULL, token_ciphertext = NULL WHERE id = :id "
            "AND status IN ('created', 'opened') AND expires_at <= :now"
        ),
        {"id": invitation_id, "now": now},
    )


def expire_due_by_token(
    connection: Connection, token_hash: str, now: datetime
) -> None:
    connection.execute(
        text(
            "UPDATE invitations SET status = 'expired', expired_at = :now, "
            "token_hash = NULL, token_ciphertext = NULL WHERE token_hash = :token_hash "
            "AND status IN ('created', 'opened') AND expires_at <= :now"
        ),
        {"token_hash": token_hash, "now": now},
    )


USABLE_INVITATION_STATUSES = ("created", "opened")


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
    if status not in USABLE_INVITATION_STATUSES:
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
    if status not in USABLE_INVITATION_STATUSES:
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


def get_active_invitation_by_token(
    database_url: str, raw_token: str
) -> dict[str, str] | None:
    token_hash = sha256(raw_token.encode()).hexdigest()
    with db_connection(database_url) as connection:
        return open_by_token(
            connection, token_hash, datetime.now(timezone.utc)
        )


def get_tutor_invitation(
    database_url: str, invitation_id: str
) -> dict[str, str | datetime | None] | None:
    with db_connection(database_url) as connection:
        expire_due_by_id(connection, invitation_id, datetime.now(timezone.utc))
        invitation = connection.execute(
            text(
                "SELECT id, email, display_name, shared_personal_message, "
                "private_tutor_note, status, created_at, first_opened_at, "
                "claimed_at, expired_at, revoked_at, expires_at FROM invitations "
                "WHERE id = :id"
            ),
            {"id": invitation_id},
        ).mappings().first()
        return dict(invitation) if invitation is not None else None


def retrieve_invitation_link(
    database_url: str, invitation_id: str, encryption_key: str
) -> str | None:
    with db_connection(database_url) as connection:
        expire_due_by_id(connection, invitation_id, datetime.now(timezone.utc))
        invitation = connection.execute(
            text(
                "SELECT token_ciphertext FROM invitations WHERE id = :id "
                "AND status IN ('created', 'opened')"
            ),
            {"id": invitation_id},
        ).mappings().first()
        if invitation is None or invitation["token_ciphertext"] is None:
            return None
        raw_token = decrypt_invitation_token(
            invitation["token_ciphertext"], encryption_key
        )
        return f"/invite/{raw_token}" if raw_token is not None else None


def correct_invitation_email(
    database_url: str, invitation_id: str, email: str
) -> dict[str, str] | None:
    with db_connection(database_url) as connection:
        status = status_after_expiration(
            connection, invitation_id, datetime.now(timezone.utc)
        )
        if status is None:
            return None
        if status not in USABLE_INVITATION_STATUSES:
            return {"id": invitation_id, "email": "", "status": "conflict"}
        corrected = connection.execute(
            text(
                "UPDATE invitations SET email = :email WHERE id = :id "
                "AND status IN ('created', 'opened') "
                "RETURNING id, email, status"
            ),
            {"id": invitation_id, "email": email.strip().lower()},
        ).mappings().first()
        return dict(corrected) if corrected is not None else None


def revoke_invitation(database_url: str, invitation_id: str) -> dict[str, str] | None:
    with db_connection(database_url) as connection:
        status = revoke_by_id(
            connection, invitation_id, datetime.now(timezone.utc)
        )
        if status is None:
            return None
        return {"id": invitation_id, "status": status}


def regenerate_invitation(
    database_url: str, invitation_id: str, ttl_seconds: int, encryption_key: str
) -> dict[str, str | datetime] | None:
    raw_token = secrets.token_urlsafe(32)
    created_at = datetime.now(timezone.utc)
    expires_at = created_at + timedelta(seconds=ttl_seconds)
    with db_connection(database_url) as connection:
        status = regenerate_by_id(
            connection,
            invitation_id,
            sha256(raw_token.encode()).hexdigest(),
            encrypt_invitation_token(raw_token, encryption_key),
            created_at,
            expires_at,
        )
        if status is None:
            return None
        if status == "conflict":
            return {"id": invitation_id, "status": "conflict"}
        return {
            "id": invitation_id,
            "status": status,
            "invitation_url": f"/invite/{raw_token}",
            "expires_at": expires_at,
        }


def create_manual_invitation(
    database_url: str, email: str, ttl_seconds: int, encryption_key: str
) -> dict[str, str | datetime]:
    raw_token = secrets.token_urlsafe(32)
    created_at = datetime.now(timezone.utc)
    invitation = {
        "id": str(uuid4()),
        "email": email.strip().lower(),
        "status": "created",
        "token_hash": sha256(raw_token.encode()).hexdigest(),
        "token_ciphertext": encrypt_invitation_token(raw_token, encryption_key),
        "created_at": created_at,
        "expires_at": created_at + timedelta(seconds=ttl_seconds),
    }
    with db_connection(database_url) as connection:
        connection.execute(
            text(
                "INSERT INTO invitations (id, email, display_name, "
                "shared_personal_message, private_tutor_note, status, token_hash, "
                "token_ciphertext, created_at, expires_at) VALUES (:id, :email, "
                "'', '', '', :status, :token_hash, :token_ciphertext, "
                ":created_at, :expires_at)"
            ),
            invitation,
        )
    return {
        "id": invitation["id"],
        "email": invitation["email"],
        "status": invitation["status"],
        "invitation_url": f"/invite/{raw_token}",
        "expires_at": invitation["expires_at"],
    }


def create_invitation_from_inquiry(
    database_url: str, inquiry_id: str, ttl_seconds: int, encryption_key: str
) -> dict[str, str | datetime] | None:
    raw_token = secrets.token_urlsafe(32)
    created_at = datetime.now(timezone.utc)
    expires_at = created_at + timedelta(seconds=ttl_seconds)
    with db_connection(database_url) as connection:
        inquiry = connection.execute(
            text(
                "UPDATE inquiries SET status = 'invited' WHERE id = :id "
                "AND status = 'new' RETURNING email"
            ),
            {"id": inquiry_id},
        ).mappings().first()
        if inquiry is None:
            return None
        invitation_id = str(uuid4())
        connection.execute(
            text(
                "INSERT INTO invitations (id, inquiry_id, email, display_name, "
                "shared_personal_message, private_tutor_note, status, token_hash, "
                "token_ciphertext, created_at, expires_at) VALUES (:id, :inquiry_id, "
                ":email, '', '', '', 'created', :token_hash, :ciphertext, "
                ":created_at, :expires_at)"
            ),
            {
                "id": invitation_id,
                "inquiry_id": inquiry_id,
                "email": inquiry["email"],
                "token_hash": sha256(raw_token.encode()).hexdigest(),
                "ciphertext": encrypt_invitation_token(raw_token, encryption_key),
                "created_at": created_at,
                "expires_at": expires_at,
            },
        )
        return {
            "id": invitation_id,
            "email": inquiry["email"],
            "status": "created",
            "invitation_url": f"/invite/{raw_token}",
            "expires_at": expires_at,
        }


def claim_direct_invitation(
    database_url: str,
    raw_token: str,
    display_name: str,
    inactivity_seconds: int,
    absolute_seconds: int,
    previous_session: str | None,
) -> dict[str, str] | None:
    now = datetime.now(timezone.utc)
    account_id = str(uuid4())
    raw_session, raw_csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    try:
        with db_connection(database_url) as connection:
            invitation = claim_by_token(
                connection,
                sha256(raw_token.encode()).hexdigest(),
                display_name,
                account_id,
                now,
            )
            if invitation is None:
                return None
            connection.execute(
                text(
                    "INSERT INTO accounts (id, email, role, display_name) "
                    "VALUES (:id, :email, 'student', :name)"
                ),
                {"id": account_id, "email": invitation["email"], "name": display_name},
            )
            connection.execute(
                text(
                    "INSERT INTO credit_ledger_entries (id, student_account_id, "
                    "event_type, quantity, reason, idempotency_key, created_at) VALUES "
                    "(:id, :student, 'credit_invitation_grant', 1, "
                    "'Invitation Claim', :key, :now)"
                ),
                {
                    "id": str(uuid4()),
                    "student": account_id,
                    "key": f"invitation:{invitation['id']}:credit",
                    "now": now,
                },
            )
            if invitation["inquiry_id"] is not None:
                connection.execute(
                    text("UPDATE inquiries SET status = 'archived' WHERE id = :id"),
                    {"id": invitation["inquiry_id"]},
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
                text(
                    "INSERT INTO authentication_sessions (id, account_id, session_hash, "
                    "csrf_hash, inactive_expires_at, absolute_expires_at, revoked_at) "
                    "VALUES (:id, :account, :session, :csrf, :inactive, :absolute, NULL)"
                ),
                {
                    "id": str(uuid4()), "account": account_id,
                    "session": sha256(raw_session.encode()).hexdigest(),
                    "csrf": sha256(raw_csrf.encode()).hexdigest(),
                    "inactive": now + timedelta(seconds=inactivity_seconds),
                    "absolute": now + timedelta(seconds=absolute_seconds),
                },
            )
            return {"status": "claimed", "role": "student", "email": invitation["email"],
                    "display_name": display_name, "session": raw_session, "csrf_token": raw_csrf}
    except IntegrityError:
        raise InvitationClaimConflict from None
