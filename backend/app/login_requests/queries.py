from datetime import datetime, timezone

from sqlalchemy import text

from app.database import db_connection


def active_login_requests(database_url: str) -> list[dict[str, str]]:
    with db_connection(database_url, mode="read") as connection:
        rows = connection.execute(
            text(
                "SELECT login_requests.id, accounts.email, requested_at, "
                "CASE WHEN magic_link_token_id IS NULL THEN 'pending' ELSE 'generated' END AS status "
                "FROM login_requests JOIN accounts ON accounts.id = login_requests.account_id "
                "LEFT JOIN magic_link_tokens ON magic_link_tokens.id = magic_link_token_id "
                "WHERE dismissed_at IS NULL AND (magic_link_token_id IS NULL OR "
                "(consumed_at IS NULL AND expires_at > :now)) ORDER BY requested_at"
            ),
            {"now": datetime.now(timezone.utc)},
        ).mappings()
        return [dict(row) for row in rows]
