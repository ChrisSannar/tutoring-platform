from uuid import UUID

import httpx
import pytest

from app.main import create_app


@pytest.mark.anyio
async def test_unknown_api_route_returns_a_sanitized_error() -> None:
    transport = httpx.ASGITransport(app=create_app())
    async with httpx.AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as client:
        response = await client.get("/api/missing?token=must-not-leak")

    assert response.status_code == 404
    assert response.json().keys() == {"code", "message", "request_id"}
    assert response.json()["code"] == "not_found"
    assert response.json()["message"] == "Resource not found"
    request_id = UUID(response.json()["request_id"])
    assert response.headers["X-Request-ID"] == str(request_id)
    assert "must-not-leak" not in response.text
