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
                "bookings": connection.execute(
                    text(
                        "SELECT COUNT(*) FROM bookings "
                        "WHERE student_account_id = :student_account_id"
                    ),
                    {"student_account_id": student_account_id},
                ).scalar_one(),
            }
            inquiry_ids = connection.execute(text(
                "SELECT inquiry_id FROM invitations WHERE claimed_account_id = :student_account_id AND inquiry_id IS NOT NULL"
            ), {"student_account_id": student_account_id}).scalars().all()
            for statement in [
                "DELETE FROM refund_evidence WHERE refund_request_id IN (SELECT id FROM refund_requests WHERE student_account_id = :student_account_id)",
                "DELETE FROM refund_requests WHERE student_account_id = :student_account_id",
                "DELETE FROM lesson_notes WHERE booking_id IN (SELECT id FROM bookings WHERE student_account_id = :student_account_id)",
                "DELETE FROM payment_evidence WHERE booking_id IN (SELECT id FROM bookings WHERE student_account_id = :student_account_id)",
                "DELETE FROM booking_change_receipts WHERE booking_id IN (SELECT id FROM bookings WHERE student_account_id = :student_account_id)",
                "DELETE FROM bookings WHERE student_account_id = :student_account_id",
                "DELETE FROM checkout_sessions WHERE student_account_id = :student_account_id",
                "DELETE FROM slot_holds WHERE student_account_id = :student_account_id",
                "DELETE FROM credit_ledger_entries WHERE student_account_id = :student_account_id",
                "DELETE FROM login_requests WHERE account_id = :student_account_id",
                "DELETE FROM invitations WHERE claimed_account_id = :student_account_id",
            ]:
                connection.execute(text(statement), {"student_account_id": student_account_id})
            for inquiry_id in inquiry_ids:
                connection.execute(text("DELETE FROM inquiries WHERE id = :id"), {"id": inquiry_id})
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
