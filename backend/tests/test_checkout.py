import asyncio
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import json
from pathlib import Path

from alembic import command
from alembic.config import Config
import httpx
import pytest
from sqlalchemy import create_engine, text

from app.authentication import issue_magic_link
from app.checkout.provider import create_provider_checkout
from app.config import get_settings
from app.main import create_app


async def checkout_clients(monkeypatch, tmp_path: Path):
    database_url = f"sqlite:///{tmp_path / 'checkout.sqlite3'}"
    config = Config("backend/alembic.ini")
    config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(config, "head")
    engine = create_engine(database_url)
    with engine.begin() as connection:
        connection.execute(text(
            "INSERT INTO accounts (id, email, role, display_name) VALUES "
            "('student', 'student@example.com', 'student', 'Student'), "
            "('other', 'other@example.com', 'student', 'Other')"
        ))
        connection.execute(text(
            "INSERT INTO availability_windows (id, weekday, start_time, end_time) "
            "VALUES ('monday', 0, '09:00', '11:00')"
        ))
        connection.execute(text(
            "UPDATE tutor_settings SET session_price_cents = 8250, default_meeting_details = 'Paid room' WHERE id = 1"
        ))
    engine.dispose()
    monkeypatch.setenv("TUTORING_ENVIRONMENT", "test")
    monkeypatch.setenv("TUTORING_DATABASE_URL", database_url)
    monkeypatch.setenv("TUTORING_APPLICATION_ORIGIN", "http://testserver")
    monkeypatch.setenv("TUTORING_STRIPE_WEBHOOK_SECRET", "signed-test-secret")
    get_settings.cache_clear()
    app = create_app()
    clock = [datetime(2026, 7, 19, 8, tzinfo=timezone.utc)]
    app.state.context.now = lambda: clock[0]
    transport = httpx.ASGITransport(app=app)

    async def authenticate(email: str):
        client = httpx.AsyncClient(transport=transport, base_url="http://testserver")
        token = issue_magic_link(database_url, email, 900)
        response = await client.post("/api/auth/magic-links/confirm", json={"token": token})
        return client, response.json()["csrf_token"]

    student, csrf = await authenticate("student@example.com")
    other, other_csrf = await authenticate("other@example.com")
    return student, csrf, other, other_csrf, database_url, clock


def signed_event(event: dict, timestamp: str = "1784448000") -> tuple[bytes, str]:
    body = json.dumps(event, separators=(",", ":")).encode()
    signature = hmac.new(
        b"signed-test-secret", timestamp.encode() + b"." + body, hashlib.sha256
    ).hexdigest()
    return body, f"t={timestamp},v1={signature}"


def test_stripe_checkout_adapter_uses_server_amount_and_metadata(monkeypatch) -> None:
    captured = {}

    class Response:
        def __enter__(self): return self
        def __exit__(self, *_): return None
        def read(self): return b'{"id":"cs_live_one","url":"https://checkout.stripe.com/c/pay/one"}'

    def fake_urlopen(request, timeout):
        captured.update(url=request.full_url, headers=dict(request.header_items()), body=request.data, timeout=timeout)
        return Response()

    monkeypatch.setattr("app.checkout.provider.urlopen", fake_urlopen)
    provider_id, url = create_provider_checkout(
        "stripe", "sk_test_private", "https://tutor.example", 8250, "USD", "student", "2026-07-20T14:00:00Z"
    )
    fields = captured["body"].decode()

    assert (provider_id, url) == ("cs_live_one", "https://checkout.stripe.com/c/pay/one")
    assert captured["url"] == "https://api.stripe.com/v1/checkout/sessions"
    assert captured["headers"]["Authorization"] == "Bearer sk_test_private"
    assert "unit_amount%5D=8250" in fields and "currency%5D=usd" in fields
    assert "metadata%5Bstudent_id%5D=student" in fields
    assert "metadata%5Bstart_at%5D=2026-07-20T14%3A00%3A00Z" in fields


@pytest.mark.anyio
async def test_checkout_hold_status_only_return_and_signed_fulfillment(monkeypatch, tmp_path: Path) -> None:
    student, csrf, other, _, database_url, _ = await checkout_clients(monkeypatch, tmp_path)
    headers = {"Origin": "http://testserver", "X-CSRF-Token": csrf, "Idempotency-Key": "checkout-one"}
    try:
        tampered = await student.post(
            "/api/student/checkouts", headers={**headers, "Idempotency-Key": "tampered"},
            json={"start_at": "2026-07-20T14:00:00Z", "focus": "Paid lesson", "amount": 1},
        )
        checkout = await student.post(
            "/api/student/checkouts", headers=headers,
            json={"start_at": "2026-07-20T14:00:00Z", "focus": "Paid lesson"},
        )
        other_slots = await other.get("/api/student/bookable-slots")
        browser_return = await student.get(
            f"/api/student/checkouts/{checkout.json()['checkout_session_id']}"
        )
        engine = create_engine(database_url)
        with engine.connect() as connection:
            before_webhook = connection.execute(text("SELECT COUNT(*) FROM bookings")).scalar_one()
        event = {
            "id": "evt_paid_one", "type": "checkout.session.completed",
            "data": {"object": {"id": checkout.json()["checkout_session_id"],
                     "metadata": {"student_id": "student", "start_at": "2026-07-20T14:00:00Z"},
                     "currency": "usd", "amount_total": 8250, "payment_intent": "pi_one"}},
        }
        body, signature = signed_event(event)
        invalid = await student.post("/api/stripe/webhook", content=body, headers={"Stripe-Signature": "wrong"})
        first, duplicate = await asyncio.gather(
            student.post("/api/stripe/webhook", content=body, headers={"Stripe-Signature": signature}),
            student.post("/api/stripe/webhook", content=body, headers={"Stripe-Signature": signature}),
        )
        with engine.connect() as connection:
            bookings = connection.execute(text("SELECT funding_kind, price_cents_snapshot FROM bookings")).all()
            evidence = connection.execute(text("SELECT provider_payment_id, amount_cents FROM payment_evidence")).all()
            holds = connection.execute(text("SELECT COUNT(*) FROM slot_holds")).scalar_one()
        engine.dispose()
    finally:
        await student.aclose(); await other.aclose(); get_settings.cache_clear()

    assert tampered.status_code == 422 and checkout.status_code == 201
    assert checkout.json()["amount_cents"] == 8250 and checkout.json()["currency"] == "USD"
    assert checkout.json()["checkout_url"].startswith("/checkout/fake/")
    assert all(slot["start_at"] != "2026-07-20T14:00:00Z" for slot in other_slots.json()["slots"])
    assert browser_return.json()["status"] == "pending" and before_webhook == 0
    assert invalid.status_code == 400
    assert sorted([first.status_code, duplicate.status_code]) == [200, 200]
    assert bookings == [("paid", 8250)]
    assert evidence == [("pi_one", 8250)] and holds == 0


@pytest.mark.anyio
async def test_checkout_mismatch_and_expiry_release_holds(monkeypatch, tmp_path: Path) -> None:
    student, csrf, other, _, _, clock = await checkout_clients(monkeypatch, tmp_path)
    base = {"Origin": "http://testserver", "X-CSRF-Token": csrf}
    try:
        first = await student.post(
            "/api/student/checkouts", headers={**base, "Idempotency-Key": "mismatch"},
            json={"start_at": "2026-07-20T14:00:00Z", "focus": None},
        )
        mismatch_event = {"id": "evt_mismatch", "type": "checkout.session.completed", "data": {
            "id": first.json()["checkout_session_id"], "student_id": "student", "start_at": "2026-07-20T14:00:00Z",
            "currency": "USD", "amount_total": 1, "payment_intent": "pi_bad"}}
        body, signature = signed_event(mismatch_event)
        mismatch = await student.post("/api/stripe/webhook", content=body, headers={"Stripe-Signature": signature})
        released = await other.get("/api/student/bookable-slots")

        second = await student.post(
            "/api/student/checkouts", headers={**base, "Idempotency-Key": "expires"},
            json={"start_at": "2026-07-20T15:00:00Z", "focus": None},
        )
        clock[0] += timedelta(minutes=31)
        expired = await student.get(f"/api/student/checkouts/{second.json()['checkout_session_id']}")
        after_expiry = await other.get("/api/student/bookable-slots")

        reconciled_checkout = await student.post(
            "/api/student/checkouts", headers={**base, "Idempotency-Key": "provider-expiry"},
            json={"start_at": "2026-07-20T14:00:00Z", "focus": None},
        )
        expired_event = {"id": "evt_expired", "type": "checkout.session.expired", "data": {
            "object": {"id": reconciled_checkout.json()["checkout_session_id"]}}}
        expired_body, expired_signature = signed_event(expired_event, "1784449860")
        reconciled = await student.post(
            "/api/stripe/webhook", content=expired_body, headers={"Stripe-Signature": expired_signature}
        )
        after_reconciliation = await other.get("/api/student/bookable-slots")
    finally:
        await student.aclose(); await other.aclose(); get_settings.cache_clear()

    assert mismatch.status_code == 409
    assert any(slot["start_at"] == "2026-07-20T14:00:00Z" for slot in released.json()["slots"])
    assert expired.json()["status"] == "expired"
    assert any(slot["start_at"] == "2026-07-20T15:00:00Z" for slot in after_expiry.json()["slots"])
    assert reconciled.json() == {"status": "expired"}
    assert any(slot["start_at"] == "2026-07-20T14:00:00Z" for slot in after_reconciliation.json()["slots"])


@pytest.mark.anyio
async def test_concurrent_checkout_starts_create_only_one_hold(monkeypatch, tmp_path: Path) -> None:
    student, csrf, other, other_csrf, database_url, _ = await checkout_clients(monkeypatch, tmp_path)
    payload = {"start_at": "2026-07-20T14:00:00Z", "focus": None}
    try:
        first, second = await asyncio.gather(
            student.post("/api/student/checkouts", headers={"Origin": "http://testserver", "X-CSRF-Token": csrf, "Idempotency-Key": "race-one"}, json=payload),
            other.post("/api/student/checkouts", headers={"Origin": "http://testserver", "X-CSRF-Token": other_csrf, "Idempotency-Key": "race-two"}, json=payload),
        )
        engine = create_engine(database_url)
        with engine.connect() as connection:
            holds = connection.execute(text("SELECT COUNT(*) FROM slot_holds")).scalar_one()
        engine.dispose()
    finally:
        await student.aclose(); await other.aclose(); get_settings.cache_clear()

    assert sorted([first.status_code, second.status_code]) == [201, 409]
    assert holds == 1
