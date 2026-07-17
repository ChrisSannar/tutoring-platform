from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import create_engine, text


def aware(value) -> datetime:
    if isinstance(value, str): value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


def record_event(connection, event_id: str, outcome: str, now: datetime) -> None:
    connection.execute(text(
        "INSERT INTO stripe_events (provider_event_id, outcome, created_at) VALUES (:id, :outcome, :now)"
    ), {"id": event_id, "outcome": outcome, "now": now})


def fulfill_event(database_url: str, event: dict, now: datetime) -> str:
    event_id, event_type, envelope = event.get("id"), event.get("type"), event.get("data", {})
    data = envelope.get("object", envelope) if isinstance(envelope, dict) else {}
    metadata = data.get("metadata", {}) if isinstance(data.get("metadata", {}), dict) else {}
    if not isinstance(event_id, str): return "mismatch"
    engine, connection = create_engine(database_url), None
    try:
        connection = engine.connect(); connection.exec_driver_sql("BEGIN IMMEDIATE")
        if connection.execute(text("SELECT 1 FROM stripe_events WHERE provider_event_id = :id"), {"id": event_id}).first():
            connection.commit(); return "duplicate"
        checkout = connection.execute(text("SELECT * FROM checkout_sessions WHERE provider_session_id = :id"), {"id": data.get("id")}).mappings().first()
        if checkout is None:
            record_event(connection, event_id, "mismatch", now); connection.commit(); return "mismatch"
        if event_type == "checkout.session.expired":
            connection.execute(text("UPDATE checkout_sessions SET status = 'expired' WHERE id = :id"), {"id": checkout["id"]})
            connection.execute(text("DELETE FROM slot_holds WHERE id = :id"), {"id": checkout["slot_hold_id"]})
            record_event(connection, event_id, "expired", now); connection.commit(); return "expired"
        if checkout["status"] == "fulfilled":
            record_event(connection, event_id, "duplicate", now); connection.commit(); return "duplicate"
        expected = (checkout["student_account_id"], aware(checkout["start_at"]), checkout["currency"], checkout["amount_cents"])
        try: received_start = aware(data.get("start_at", metadata.get("start_at")))
        except (TypeError, ValueError): received_start = None
        received = (
            data.get("student_id", metadata.get("student_id")),
            received_start,
            str(data.get("currency", "")).upper(),
            data.get("amount_total"),
        )
        valid = event_type == "checkout.session.completed" and expected == received and isinstance(data.get("payment_intent"), str)
        if checkout["status"] != "pending" or aware(checkout["expires_at"]) <= now or not valid:
            connection.execute(text("UPDATE checkout_sessions SET status = 'mismatch' WHERE id = :id"), {"id": checkout["id"]})
            connection.execute(text("DELETE FROM slot_holds WHERE id = :id"), {"id": checkout["slot_hold_id"]})
            record_event(connection, event_id, "mismatch", now); connection.commit(); return "mismatch"
        conflict = connection.execute(text(
            "SELECT 1 FROM bookings WHERE status = 'upcoming' AND start_at < :end AND end_at > :start "
            "UNION ALL SELECT 1 FROM blocked_times WHERE start_at < :end AND end_at > :start "
            "UNION ALL SELECT 1 FROM slot_holds WHERE id != :hold AND expires_at > :now AND start_at < :end AND end_at > :start LIMIT 1"
        ), {"start": checkout["start_at"], "end": checkout["end_at"], "hold": checkout["slot_hold_id"], "now": now}).first()
        upcoming = connection.execute(text("SELECT 1 FROM bookings WHERE student_account_id = :student AND status = 'upcoming'"), {"student": checkout["student_account_id"]}).first()
        if conflict is not None or upcoming is not None:
            connection.execute(text("UPDATE checkout_sessions SET status = 'mismatch' WHERE id = :id"), {"id": checkout["id"]})
            connection.execute(text("DELETE FROM slot_holds WHERE id = :id"), {"id": checkout["slot_hold_id"]})
            record_event(connection, event_id, "mismatch", now); connection.commit(); return "mismatch"
        booking_id = str(uuid4())
        connection.execute(text(
            "INSERT INTO bookings (id, student_account_id, start_at, end_at, status, funding_kind, focus, meeting_details_snapshot, "
            "price_cents_snapshot, currency_snapshot, idempotency_key, created_at) VALUES (:id, :student, :start, :end, 'upcoming', "
            "'paid', :focus, :details, :amount, :currency, :key, :now)"
        ), {"id": booking_id, "student": checkout["student_account_id"], "start": checkout["start_at"], "end": checkout["end_at"],
            "focus": checkout["focus"], "details": checkout["meeting_details_snapshot"], "amount": checkout["amount_cents"],
            "currency": checkout["currency"], "key": f"stripe:{checkout['provider_session_id']}", "now": now})
        connection.execute(text(
            "INSERT INTO payment_evidence (id, booking_id, checkout_session_id, provider_payment_id, provider_event_id, amount_cents, currency, created_at) "
            "VALUES (:id, :booking, :checkout, :payment, :event, :amount, :currency, :now)"
        ), {"id": str(uuid4()), "booking": booking_id, "checkout": checkout["provider_session_id"], "payment": data["payment_intent"],
            "event": event_id, "amount": checkout["amount_cents"], "currency": checkout["currency"], "now": now})
        connection.execute(text("UPDATE checkout_sessions SET status = 'fulfilled' WHERE id = :id"), {"id": checkout["id"]})
        connection.execute(text("DELETE FROM slot_holds WHERE id = :id"), {"id": checkout["slot_hold_id"]})
        record_event(connection, event_id, "fulfilled", now); connection.commit(); return "fulfilled"
    except Exception:
        if connection is not None: connection.rollback()
        raise
    finally:
        if connection is not None: connection.close()
        engine.dispose()
