import pytest
from fastapi import APIRouter
from fastapi.testclient import TestClient
from pydantic import BaseModel, ValidationError

from app.core.config import Environment, Settings
from app.core.exceptions import InvalidDocumentError
from app.main import create_app


class _Body(BaseModel):
    value: int


@pytest.fixture
def client() -> TestClient:
    app = create_app(Settings(_env_file=None, environment=Environment.TESTING))

    router = APIRouter()

    @router.get("/_test/app-error")
    async def raise_app_error():
        raise InvalidDocumentError("Image too blurry", details={"field": "image"})

    @router.get("/_test/crash")
    async def raise_crash():
        raise RuntimeError("boom")

    @router.post("/_test/validate")
    async def validate(body: _Body):
        return body

    app.include_router(router)
    return TestClient(app, raise_server_exceptions=False)


def test_health(client: TestClient) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
    assert resp.json()["environment"] == "testing"


def test_request_id_generated_and_echoed(client: TestClient) -> None:
    assert len(client.get("/health").headers["X-Request-ID"]) == 32
    resp = client.get("/health", headers={"X-Request-ID": "abc-123"})
    assert resp.headers["X-Request-ID"] == "abc-123"


def test_app_error_envelope(client: TestClient) -> None:
    resp = client.get("/_test/app-error", headers={"X-Request-ID": "req-1"})
    assert resp.status_code == 422
    assert resp.json() == {
        "error": {
            "code": "invalid_document",
            "message": "Image too blurry",
            "details": {"field": "image"},
            "request_id": "req-1",
        }
    }


def test_not_found_envelope(client: TestClient) -> None:
    resp = client.get("/does-not-exist")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "http_error"


def test_validation_error_envelope(client: TestClient) -> None:
    resp = client.post("/_test/validate", json={"value": "not-an-int"})
    assert resp.status_code == 422
    error = resp.json()["error"]
    assert error["code"] == "validation_error"
    assert error["details"][0]["loc"] == ["body", "value"]


def test_unhandled_exception_hides_internals(client: TestClient) -> None:
    resp = client.get("/_test/crash")
    assert resp.status_code == 500
    assert resp.json()["error"]["code"] == "internal_error"
    assert "boom" not in resp.text
    assert "X-Request-ID" in resp.headers


def test_settings_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    monkeypatch.setenv("MAX_UPLOAD_SIZE_MB", "5")
    settings = Settings(_env_file=None)
    assert settings.anthropic_api_key.get_secret_value() == "sk-test"
    assert "sk-test" not in repr(settings)
    assert settings.max_upload_size_bytes == 5 * 1024 * 1024


def test_production_requires_api_key() -> None:
    with pytest.raises(ValidationError, match="ANTHROPIC_API_KEY"):
        Settings(_env_file=None, environment=Environment.PRODUCTION)
