from sqlalchemy import text

from app.database import db_connection


def list_active_inquiries(database_url: str) -> list[dict[str, str]]:
    with db_connection(database_url, mode="read") as connection:
        rows = connection.execute(
            text(
                "SELECT inquiries.id, inquiries.email, inquiries.message, "
                "inquiries.status, invitations.id AS invitation_id FROM inquiries "
                "LEFT JOIN invitations ON invitations.inquiry_id = inquiries.id "
                "WHERE inquiries.status IN ('new', 'invited') "
                "ORDER BY inquiries.created_at, inquiries.id"
            )
        ).mappings()
        return [dict(row) for row in rows]
