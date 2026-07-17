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
