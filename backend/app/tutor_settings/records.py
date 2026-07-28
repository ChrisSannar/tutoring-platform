from sqlalchemy import text

from app.database import db_connection


def get_tutor_settings(database_url: str) -> dict[str, str | None]:
    with db_connection(database_url, mode="read") as connection:
        return dict(
            connection.execute(
                text(
                    "SELECT tutor_timezone, default_meeting_details "
                    "FROM tutor_settings WHERE id = 1"
                )
            ).mappings().one()
        )


def update_tutor_settings(
    database_url: str,
    tutor_timezone: str,
    default_meeting_details: str | None,
) -> dict[str, str | None]:
    with db_connection(database_url) as connection:
        return dict(
            connection.execute(
                text(
                    "UPDATE tutor_settings SET tutor_timezone = :timezone, "
                    "default_meeting_details = :details WHERE id = 1 RETURNING "
                    "tutor_timezone, default_meeting_details"
                ),
                {"timezone": tutor_timezone, "details": default_meeting_details},
            ).mappings().one()
        )
