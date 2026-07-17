from sqlalchemy import create_engine, text


def list_credit_ledger(
    database_url: str, student_id: str
) -> list[dict[str, object]] | None:
    engine = create_engine(database_url)
    try:
        with engine.connect() as connection:
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
    finally:
        engine.dispose()
