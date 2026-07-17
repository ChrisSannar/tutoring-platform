import json
import hashlib
import hmac
from datetime import datetime
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from uuid import uuid4


def valid_webhook_signature(body: bytes, supplied: str, secret: str, now: datetime) -> bool:
    values = {}
    for part in supplied.split(","):
        if "=" in part:
            key, value = part.split("=", 1)
            values.setdefault(key, []).append(value)
    try:
        timestamp = int(values["t"][0])
        signatures = values["v1"]
    except (KeyError, ValueError):
        return False
    if abs(int(now.timestamp()) - timestamp) > 300:
        return False
    payload = str(timestamp).encode() + b"." + body
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return bool(secret) and any(hmac.compare_digest(signature, expected) for signature in signatures)


def create_fake_checkout() -> tuple[str, str]:
    session_id = f"cs_test_{uuid4().hex}"
    return session_id, f"/checkout/fake/{session_id}"


def create_provider_checkout(
    mode: str,
    secret_key: str,
    origin: str,
    amount_cents: int,
    currency: str,
    student_id: str,
    start_at: str,
) -> tuple[str, str]:
    if mode == "fake":
        return create_fake_checkout()
    fields = {
        "mode": "payment",
        "success_url": f"{origin}/checkout/return?session_id={{CHECKOUT_SESSION_ID}}",
        "cancel_url": f"{origin}/student",
        "line_items[0][price_data][currency]": currency.lower(),
        "line_items[0][price_data][unit_amount]": str(amount_cents),
        "line_items[0][price_data][product_data][name]": "Tutoring session",
        "line_items[0][quantity]": "1",
        "metadata[student_id]": student_id,
        "metadata[start_at]": start_at,
    }
    request = Request(
        "https://api.stripe.com/v1/checkout/sessions",
        data=urlencode(fields).encode(),
        headers={"Authorization": f"Bearer {secret_key}", "Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urlopen(request, timeout=10) as response:
        body = json.loads(response.read())
    return body["id"], body["url"]
