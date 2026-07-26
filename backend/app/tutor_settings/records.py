from sqlalchemy import text

from app.database import db_connection


def get_tutor_settings(database_url: str) -> dict[str, str | int | None]:
    with db_connection(database_url, mode="read") as connection:
        row = connection.execute(
            text(
                "SELECT currency, session_price_cents, tutor_timezone, "
                "default_meeting_details FROM tutor_settings WHERE id = 1"
            )
        ).mappings().one()
        return dict(row)


def update_tutor_settings(
    database_url: str,
    currency: str,
    session_price_cents: int,
    tutor_timezone: str,
    default_meeting_details: str | None,
) -> dict[str, str | int | None]:
    with db_connection(database_url) as connection:
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
