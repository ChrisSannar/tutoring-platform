from hashlib import sha256

from sqlalchemy import create_engine, text


def response(row) -> dict:
    return {key: row[key] for key in ("id", "booking_id", "amount_cents", "currency", "status", "created_at")}


def list_student_refunds(database_url: str, raw_session: str) -> list[dict]:
    engine = create_engine(database_url)
    try:
        with engine.connect() as connection:
            rows = connection.execute(text(
                "SELECT refund_requests.* FROM refund_requests JOIN authentication_sessions ON "
                "authentication_sessions.account_id = student_account_id WHERE session_hash = :hash "
                "ORDER BY refund_requests.created_at DESC LIMIT 50"
            ), {"hash": sha256(raw_session.encode()).hexdigest()}).mappings()
            return [response(row) for row in rows]
    finally:
        engine.dispose()


def list_tutor_refunds(database_url: str) -> list[dict]:
    engine = create_engine(database_url)
    try:
        with engine.connect() as connection:
            rows = connection.execute(text(
                "SELECT refund_requests.*, accounts.display_name FROM refund_requests JOIN accounts ON "
                "accounts.id = student_account_id ORDER BY CASE status WHEN 'pending' THEN 0 ELSE 1 END, "
                "refund_requests.created_at DESC LIMIT 100"
            )).mappings()
            return [{**response(row), "student": {"id": row["student_account_id"], "display_name": row["display_name"]}} for row in rows]
    finally:
        engine.dispose()
