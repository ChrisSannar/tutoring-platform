from uuid import UUID

from fastapi.testclient import TestClient

from app.main import create_app


def test_unknown_api_route_returns_a_sanitized_error() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/api/missing?token=must-not-leak")

    assert response.status_code == 404
    assert response.json().keys() == {"code", "message", "request_id"}
    assert response.json()["code"] == "not_found"
    assert response.json()["message"] == "Resource not found"
    request_id = UUID(response.json()["request_id"])
    assert response.headers["X-Request-ID"] == str(request_id)
    assert "must-not-leak" not in response.text
