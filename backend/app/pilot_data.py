from hashlib import sha256

from sqlalchemy import create_engine, text


def delete_student_pilot_data(
    database_url: str, student_account_id: str
) -> dict[str, int] | None:
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            student = connection.execute(
                text(
                    "SELECT email FROM accounts WHERE id = :student_account_id "
                    "AND role = 'student'"
                ),
                {"student_account_id": student_account_id},
            ).mappings().first()
            if student is None:
                return None

            counts = {
                "invitations": connection.execute(
                    text(
                        "SELECT COUNT(*) FROM invitations "
                        "WHERE claimed_account_id = :student_account_id"
                    ),
                    {"student_account_id": student_account_id},
                ).scalar_one(),
                "student_sessions": connection.execute(
                    text(
                        "SELECT COUNT(*) FROM authentication_sessions "
                        "WHERE account_id = :student_account_id"
                    ),
                    {"student_account_id": student_account_id},
                ).scalar_one(),
                "session_requests": connection.execute(
                    text(
                        "SELECT COUNT(*) FROM session_requests "
                        "WHERE student_account_id = :student_account_id"
                    ),
                    {"student_account_id": student_account_id},
                ).scalar_one(),
            }
            connection.execute(
                text(
                    "DELETE FROM invitation_claim_tokens WHERE invitation_id IN "
                    "(SELECT id FROM invitations "
                    "WHERE claimed_account_id = :student_account_id)"
                ),
                {"student_account_id": student_account_id},
            )
            connection.execute(
                text(
                    "DELETE FROM invitations "
                    "WHERE claimed_account_id = :student_account_id"
                ),
                {"student_account_id": student_account_id},
            )
            connection.execute(
                text(
                    "DELETE FROM session_requests "
                    "WHERE student_account_id = :student_account_id"
                ),
                {"student_account_id": student_account_id},
            )
            connection.execute(
                text(
                    "DELETE FROM authentication_sessions "
                    "WHERE account_id = :student_account_id"
                ),
                {"student_account_id": student_account_id},
            )
            connection.execute(
                text("DELETE FROM magic_link_tokens WHERE account_id = :student_account_id"),
                {"student_account_id": student_account_id},
            )
            connection.execute(
                text("DELETE FROM authentication_request_events WHERE email_hash = :email_hash"),
                {"email_hash": sha256(student["email"].encode()).hexdigest()},
            )
            connection.execute(
                text("DELETE FROM accounts WHERE id = :student_account_id"),
                {"student_account_id": student_account_id},
            )
            return counts
    finally:
        engine.dispose()
