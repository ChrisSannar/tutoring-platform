from hashlib import sha256

from sqlalchemy import create_engine, text


def student_funding_summary(database_url: str, raw_session: str) -> dict[str, str | int]:
    engine = create_engine(database_url)
    try:
        with engine.connect() as connection:
            summary = connection.execute(
                text(
                    "SELECT COALESCE(SUM(CASE WHEN event_type = 'promotion_granted' "
                    "THEN quantity ELSE 0 END), 0) AS promotion, "
                    "COALESCE(SUM(CASE WHEN event_type LIKE 'credit_%' THEN quantity "
                    "ELSE 0 END), 0) AS credits FROM credit_ledger_entries JOIN "
                    "authentication_sessions ON authentication_sessions.account_id = "
                    "credit_ledger_entries.student_account_id WHERE "
                    "authentication_sessions.session_hash = :session_hash"
                ),
                {"session_hash": sha256(raw_session.encode()).hexdigest()},
            ).mappings().one()
            return {
                "first_session_promotion": (
                    "available" if summary["promotion"] > 0 else "unavailable"
                ),
                "session_credits": summary["credits"],
            }
    finally:
        engine.dispose()
