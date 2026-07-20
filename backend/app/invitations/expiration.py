from datetime import datetime

from sqlalchemy import text
from sqlalchemy.engine import Connection


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
