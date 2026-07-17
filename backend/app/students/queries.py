from sqlalchemy import create_engine, text


def list_students(database_url: str) -> list[dict[str, str]]:
    engine = create_engine(database_url)
    try:
        with engine.connect() as connection:
            students = connection.execute(
                text(
                    "SELECT id, email, display_name FROM accounts "
                    "WHERE role = 'student' ORDER BY display_name, email"
                )
            ).mappings()
            return [dict(student) for student in students]
    finally:
        engine.dispose()


def get_student_detail(
    database_url: str, student_id: str
) -> dict[str, object] | None:
    engine = create_engine(database_url)
    try:
        with engine.connect() as connection:
            student = connection.execute(
                text(
                    "SELECT accounts.id, accounts.email, accounts.display_name, "
                    "COALESCE(SUM(CASE WHEN event_type LIKE 'promotion_%' THEN "
                    "quantity ELSE 0 END), 0) AS promotion, COALESCE(SUM(CASE WHEN "
                    "event_type LIKE 'credit_%' THEN quantity ELSE 0 END), 0) AS credits "
                    "FROM accounts LEFT JOIN credit_ledger_entries ON accounts.id = "
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
            refunds = connection.execute(
                text(
                    "SELECT id FROM refund_requests WHERE student_account_id = :id "
                    "AND status = 'pending' ORDER BY created_at DESC LIMIT 20"
                ),
                {"id": student_id},
            ).mappings()
            return {
                "id": student["id"],
                "email": student["email"],
                "display_name": student["display_name"],
                "funding": {
                    "first_session_promotion": (
                        "available" if student["promotion"] > 0 else "unavailable"
                    ),
                    "session_credits": student["credits"],
                },
                "pending_refund_requests": [dict(refund) for refund in refunds],
                "upcoming_booking": None if booking is None else dict(booking),
            }
    finally:
        engine.dispose()
