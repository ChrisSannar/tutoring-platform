from hashlib import sha256

from sqlalchemy import create_engine, text

def get_active_invitation_by_token(
    database_url: str, raw_token: str
) -> dict[str, str] | None:
    token_hash = sha256(raw_token.encode()).hexdigest()
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "UPDATE invitations SET status = 'expired', token_hash = NULL, "
                    "token_ciphertext = NULL WHERE token_hash = :token_hash "
                    "AND status IN ('active', 'created', 'opened') "
                    "AND expires_at <= CURRENT_TIMESTAMP"
                ),
                {"token_hash": token_hash},
            )
            invitation = connection.execute(
                text(
                    "SELECT email, display_name, shared_personal_message "
                    "FROM invitations WHERE token_hash = :token_hash "
                    "AND status IN ('active', 'created', 'opened') "
                    "AND expires_at > CURRENT_TIMESTAMP"
                ),
                {"token_hash": token_hash},
            ).mappings().first()
            if invitation is None:
                return None
            connection.execute(
                text(
                    "UPDATE invitations SET status = 'opened' "
                    "WHERE token_hash = :token_hash AND status = 'created'"
                ),
                {"token_hash": token_hash},
            )
            return dict(invitation)
    finally:
        engine.dispose()
