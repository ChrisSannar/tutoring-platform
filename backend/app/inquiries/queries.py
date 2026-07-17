from sqlalchemy import create_engine, text


def list_active_inquiries(database_url: str) -> list[dict[str, str]]:
    engine = create_engine(database_url)
    try:
        with engine.connect() as connection:
            rows = connection.execute(
                text(
                    "SELECT id, email, message, status FROM inquiries "
                    "WHERE status IN ('new', 'invited') ORDER BY created_at, id"
                )
            ).mappings()
            return [dict(row) for row in rows]
    finally:
        engine.dispose()
