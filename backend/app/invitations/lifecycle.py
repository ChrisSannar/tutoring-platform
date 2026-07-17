
from sqlalchemy import create_engine, text

def correct_invitation_email(
    database_url: str, invitation_id: str, email: str
) -> dict[str, str] | None:
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            corrected = connection.execute(
                text(
                    "UPDATE invitations SET email = :email WHERE id = :id "
                    "AND status IN ('draft', 'active', 'created', 'opened') "
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
            revoked = connection.execute(
                text(
                    "UPDATE invitations SET status = 'revoked', token_hash = NULL, "
                    "token_ciphertext = NULL WHERE id = :id AND status IN "
                    "('active', 'created', 'opened') RETURNING id, status"
                ),
                {"id": invitation_id},
            ).mappings().first()
            return dict(revoked) if revoked is not None else None
    finally:
        engine.dispose()
