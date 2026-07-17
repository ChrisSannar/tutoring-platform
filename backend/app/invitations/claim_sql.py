CLAIM_INVITATION = (
    "UPDATE invitations SET status = 'claimed', display_name = :display_name, "
    "claimed_account_id = :account_id, token_hash = NULL "
    "WHERE status = 'active' AND id = (SELECT invitation_id "
    "FROM invitation_claim_tokens WHERE token_hash = :token_hash "
    "AND consumed_at IS NULL AND expires_at > :now) RETURNING id, email"
)

CREATE_ACCOUNT = (
    "INSERT INTO accounts (id, email, role, display_name) "
    "VALUES (:id, :email, 'student', :display_name)"
)

CREATE_SESSION = (
    "INSERT INTO authentication_sessions "
    "(id, account_id, session_hash, csrf_hash, inactive_expires_at, "
    "absolute_expires_at, revoked_at) VALUES (:id, :account_id, "
    ":session_hash, :csrf_hash, :inactive, :absolute, NULL)"
)
