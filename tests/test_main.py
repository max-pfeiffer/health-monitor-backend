import tomllib
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine

import app.main as app_main
from app.config import settings
from app.main import app


def test_root_redirects_to_docs(client: TestClient):
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/docs"


def test_healthz_requires_no_auth(client_no_auth: TestClient):
    response = client_no_auth.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readyz_with_reachable_database(
    client_no_auth: TestClient, engine, monkeypatch
):
    monkeypatch.setattr(app_main, "engine", engine)
    response = client_no_auth.get("/readyz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readyz_with_unreachable_database(client_no_auth: TestClient, monkeypatch):
    unreachable_engine = create_engine(
        "postgresql+psycopg2://postgres:postgres@localhost:1/health_monitor"
    )
    monkeypatch.setattr(app_main, "engine", unreachable_engine)
    response = client_no_auth.get("/readyz")
    assert response.status_code == 503


def test_app_version_matches_pyproject():
    pyproject = tomllib.loads(
        (Path(__file__).resolve().parent.parent / "pyproject.toml").read_text()
    )
    assert app.version == pyproject["project"]["version"]


def test_cors_preflight_allows_configured_origin(client: TestClient):
    origin = settings.cors_allowed_origins_list[0]
    response = client.options(
        "/api/v1/blood_pressure",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin
    allowed_methods = response.headers["access-control-allow-methods"]
    for method in ("GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"):
        assert method in allowed_methods
    allowed_headers = response.headers["access-control-allow-headers"].lower()
    assert "authorization" in allowed_headers
    assert "content-type" in allowed_headers
    assert "access-control-allow-credentials" not in response.headers


def test_cors_disallowed_origin_has_no_cors_headers(client: TestClient):
    response = client.options(
        "/api/v1/blood_pressure",
        headers={
            "Origin": "http://evil.example.com",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert "access-control-allow-origin" not in response.headers


def test_cors_parses_comma_separated_origins():
    from app.config import Settings

    s = Settings(cors_allowed_origins="http://a.test, http://b.test ,http://c.test")
    assert s.cors_allowed_origins_list == [
        "http://a.test",
        "http://b.test",
        "http://c.test",
    ]
