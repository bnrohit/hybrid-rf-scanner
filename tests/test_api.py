from fastapi.testclient import TestClient

from hybrid_scanner.api import build_app
from hybrid_scanner.state import StatusStore


def test_public_health_is_minimal_and_metrics_are_protected():
    store = StatusStore()
    store.update(healthy=True, ready=True, last_error="secret detail")
    client = TestClient(
        build_app(store, token="test-token", host="0.0.0.0", allow_loopback_without_token=False)
    )
    assert client.get("/health").json() == {"ok": True, "ready": True}
    assert client.get("/metrics").status_code == 401
    assert client.get("/metrics", headers={"Authorization": "Bearer test-token"}).status_code == 200


def test_remote_bind_without_token_is_rejected():
    store = StatusStore()
    try:
        build_app(store, token=None, host="0.0.0.0", allow_loopback_without_token=True)
    except RuntimeError:
        pass
    else:
        raise AssertionError("remote unauthenticated bind must be rejected")
