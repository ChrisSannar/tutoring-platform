import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def refund_payment(mode: str, secret: str, payment_id: str, amount: int, currency: str, key: str) -> tuple[bool, str | None]:
    if mode == "fake":
        return True, f"re_test_{key}"
    request = Request(
        "https://api.stripe.com/v1/refunds",
        data=urlencode({"payment_intent": payment_id, "amount": amount}).encode(),
        headers={
            "Authorization": f"Bearer {secret}",
            "Content-Type": "application/x-www-form-urlencoded",
            "Idempotency-Key": key,
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=10) as response:
            result = json.loads(response.read())
    except (OSError, ValueError, KeyError):
        return False, None
    return result.get("status") == "succeeded", result.get("id")
