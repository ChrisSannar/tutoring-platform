from sqlalchemy import text

from app.bookings import reconcile_past_bookings
from app.database import db_connection


def list_students(database_url: str) -> list[dict[str, str]]:
    with db_connection(database_url, mode="read") as connection:
        students = connection.execute(
            text(
                "SELECT id, email, display_name FROM accounts "
                "WHERE role = 'student' ORDER BY display_name, email"
            )
        ).mappings()
        return [dict(student) for student in students]


def get_student_detail(
    database_url: str, student_id: str, now
) -> dict[str, object] | None:
    with db_connection(database_url, mode="immediate") as connection:
        reconcile_past_bookings(connection, now)
        student = connection.execute(
            text(
                "SELECT accounts.id, accounts.email, accounts.display_name, "
                "COALESCE(SUM(CASE WHEN event_type LIKE 'credit_%' THEN "
                "quantity ELSE 0 END), 0) AS credits FROM accounts "
                "LEFT JOIN credit_ledger_entries ON accounts.id = "
                "credit_ledger_entries.student_account_id WHERE accounts.id = :id "
                "AND accounts.role = 'student' GROUP BY accounts.id"
            ),
            {"id": student_id},
        ).mappings().first()
        if student is None:
            return None
        booking = connection.execute(
            text(
                "SELECT id FROM bookings WHERE student_account_id = :id "
                "AND status = 'upcoming' LIMIT 1"
            ),
            {"id": student_id},
        ).mappings().first()
        return {
            "id": student["id"],
            "email": student["email"],
            "display_name": student["display_name"],
            "funding": {"session_credits": student["credits"]},
            "upcoming_booking": None if booking is None else dict(booking),
        }
