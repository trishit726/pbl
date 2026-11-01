from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from shared.config import get_settings
from shared.logging import request_log_record
from shared.middleware import RequestAuditMiddleware
from shared.rbac import require_roles


@pytest.fixture(autouse=True)
def settings(monkeypatch):
    monkeypatch.setenv("JWT_SIGNING_KEY", "test-secret")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def token(role: str) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode({
        "iss": "lms-backend", "aud": "lms-frontend", "sub": "u-1",
        "user_id": "u-1", "role": role, "device_id": "d-1", "session_id": "s-1",
        "token_type": "access", "iat": now, "exp": now + timedelta(minutes=5),
    }, "test-secret", algorithm="HS256")


def test_rbac_allows_and_denies_roles():
    app = FastAPI()
    app.get("/faculty")(lambda principal=__import__("fastapi").Depends(require_roles("faculty")): {"ok": True})
    client = TestClient(app)
    assert client.get("/faculty", headers={"Authorization": f"Bearer {token('faculty')}"}).status_code == 200
    assert client.get("/faculty", headers={"Authorization": f"Bearer {token('student')}"}).status_code == 403


def test_request_middleware_sets_id_and_emits_log(monkeypatch):
    import shared.middleware as middleware
    seen = []
    monkeypatch.setattr(middleware, "emit_request_log", seen.append)
    app = FastAPI()
    app.add_middleware(RequestAuditMiddleware)
    @app.get("/health")
    def health():
        return {"ok": True}
    response = TestClient(app).get("/health", headers={"X-Device-Id": "device-1", "X-Forwarded-For": "192.0.2.1"})
    assert response.status_code == 200
    assert response.headers["X-Request-Id"]
    assert seen[0]["device_id"] == "device-1"
    assert seen[0]["source_ip"] == "192.0.2.1"


def test_log_record_has_required_fields():
    record = request_log_record(request_id="r", user_id=None, role=None, device_id=None,
        source_ip=None, endpoint="/", method="GET", status=200,
        response_size_bytes=2, latency_ms=1.23456)
    assert {"timestamp", "request_id", "user_id", "role", "device_id", "source_ip",
            "endpoint", "method", "status", "response_size_bytes", "latency_ms"} <= record.keys()
    assert record["latency_ms"] == 1.235

