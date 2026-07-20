
from datetime import datetime, timezone

from sqlalchemy import create_engine, text

from app.invitations.transitions import (
    USABLE_INVITATION_STATUSES,
    revoke_by_id,
    status_after_expiration,
)

def correct_invitation_email(
    database_url: str, invitation_id: str, email: str
) -> dict[str, str] | None:
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
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
    finally:
        engine.dispose()

def revoke_invitation(database_url: str, invitation_id: str) -> dict[str, str] | None:
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            status = revoke_by_id(
                connection, invitation_id, datetime.now(timezone.utc)
            )
            if status is None:
                return None
            return {"id": invitation_id, "status": status}
    finally:
        engine.dispose()
