from sqlalchemy import create_engine, text


def get_tutor_settings(database_url: str) -> dict[str, str | int | None]:
    engine = create_engine(database_url)
    try:
        with engine.connect() as connection:
            row = connection.execute(
                text(
                    "SELECT currency, session_price_cents, tutor_timezone, "
                    "default_meeting_details FROM tutor_settings WHERE id = 1"
                )
            ).mappings().one()
            return dict(row)
    finally:
        engine.dispose()


def update_tutor_settings(
    database_url: str,
    currency: str,
    session_price_cents: int,
    tutor_timezone: str,
    default_meeting_details: str | None,
) -> dict[str, str | int | None]:
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            row = connection.execute(
                text(
                    "UPDATE tutor_settings SET currency = :currency, "
                    "session_price_cents = :price, tutor_timezone = :timezone, "
                    "default_meeting_details = :details WHERE id = 1 RETURNING "
                    "currency, session_price_cents, tutor_timezone, "
                    "default_meeting_details"
                ),
                {
                    "currency": currency,
                    "price": session_price_cents,
                    "timezone": tutor_timezone,
                    "details": default_meeting_details,
                },
            ).mappings().one()
            return dict(row)
    finally:
        engine.dispose()
