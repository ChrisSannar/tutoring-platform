from sqlalchemy import text

from app.bookings import reconcile_past_bookings
from app.database import db_connection


def list_credit_ledger(
    database_url: str, student_id: str, now
) -> list[dict[str, object]] | None:
    with db_connection(database_url, mode="immediate") as connection:
        reconcile_past_bookings(connection, now)
        if connection.execute(
            text("SELECT 1 FROM accounts WHERE id = :id AND role = 'student'"),
            {"id": student_id},
        ).first() is None:
            return None
        events = connection.execute(
            text(
                "SELECT id, event_type, quantity, reason, created_at FROM "
                "credit_ledger_entries WHERE student_account_id = :student "
                "ORDER BY created_at, id"
            ),
            {"student": student_id},
        ).mappings()
        return [dict(event) for event in events]
