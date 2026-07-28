from hashlib import sha256

from sqlalchemy import text

from app.bookings import reconcile_past_bookings
from app.database import db_connection


def student_funding_summary(database_url: str, raw_session: str, now) -> dict[str, int]:
    with db_connection(database_url, mode="immediate") as connection:
        reconcile_past_bookings(connection, now)
        summary = connection.execute(
            text(
                "SELECT COALESCE(SUM(quantity), 0) AS credits "
                "FROM credit_ledger_entries JOIN "
                "authentication_sessions ON authentication_sessions.account_id = "
                "credit_ledger_entries.student_account_id WHERE "
                "authentication_sessions.session_hash = :session_hash"
            ),
            {"session_hash": sha256(raw_session.encode()).hexdigest()},
        ).mappings().one()
        return {"session_credits": summary["credits"]}
