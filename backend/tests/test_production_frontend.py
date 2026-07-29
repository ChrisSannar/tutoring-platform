import pytest


@pytest.mark.anyio
async def test_production_serves_frontend_without_catching_api_routes(
    monkeypatch, testbed
) -> None:
    frontend = testbed.tmp_path / "frontend" / "dist"
    (frontend / "assets").mkdir(parents=True)
    (frontend / "index.html").write_text("<h1>Tutoring Platform</h1>")
    (frontend / "assets" / "app.js").write_text("console.log('ready')")
    monkeypatch.chdir(testbed.tmp_path)
    monkeypatch.setenv("TUTORING_ENVIRONMENT", "production")
    monkeypatch.setenv("TUTORING_DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("TUTORING_APPLICATION_ORIGIN", "https://tutor.example.com")

    async with testbed.client() as client:
        root = await client.get("/")
        browser_route = await client.get("/tutor")
        asset = await client.get("/assets/app.js")
        missing_api = await client.get("/api/does-not-exist")

    assert root.text == browser_route.text == "<h1>Tutoring Platform</h1>"
    assert asset.text == "console.log('ready')"
    assert root.headers["content-security-policy"].startswith("default-src 'self'")
    assert root.headers["x-frame-options"] == "DENY"
    assert missing_api.status_code == 404
    assert missing_api.json()["code"] == "not_found"
    assert "content-security-policy" not in missing_api.headers
