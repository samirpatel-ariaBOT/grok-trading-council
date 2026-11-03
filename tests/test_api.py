from threading import Thread
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import json
import pytest
from services.api import Application, server


@pytest.fixture
def api(tmp_path):
    app = Application(tmp_path / "demo.sqlite")
    http = server(app, 0)
    thread = Thread(target=http.serve_forever, daemon=True)
    thread.start()
    yield app, f"http://127.0.0.1:{http.server_port}"
    http.shutdown()
    http.server_close()
    thread.join()


def request(base, path, data=None, token=None, extra=None):
    headers = extra or {}
    if token:
        headers["X-GTC-Token"] = token
    if data is not None:
        headers["Content-Type"] = "application/json"
    req = Request(
        base + path,
        data=None if data is None else json.dumps(data).encode(),
        headers=headers,
    )
    try:
        with urlopen(req, timeout=5) as r:
            return r.status, r.read()
    except HTTPError as r:
        return r.code, r.read()


def test_api_read_and_security(api):
    a, base = api
    status, body = request(base, "/api/state")
    s = json.loads(body)
    assert (
        status == 200
        and s["mode"] == "DEMO"
        and s["native_operations"]["status"] == "REQUIRED_UNVERIFIED"
    )
    assert request(base, "/api/pause", {})[0] == 403
    assert (
        request(base, "/api/pause", {}, a.token, {"Origin": "https://evil.example"})[0]
        == 403
    )
    assert request(base, "/api/state", extra={"Host": "evil.example"})[0] == 403
    assert request(base, "/../config/bootstrap.json")[0] == 404
    assert request(base, "/api/live-order", {}, a.token)[0] == 400


def test_ui_actions_and_export(api):
    a, base = api
    status, body = request(
        base,
        "/api/experiment",
        {
            "name": "Test",
            "hypothesis": "Reject unless net cost-adjusted result improves on a held-out period.",
        },
        a.token,
    )
    assert status == 200 and json.loads(body)["result"]["activation"] is False
    assert request(base, "/api/settings", {"note": "Needs review"}, a.token)[0] == 200
    assert (
        request(
            base, "/api/settings", {"note": "x", "execution_enabled": True}, a.token
        )[0]
        == 400
    )
    p = a.store.all("position")[0]
    assert (
        request(base, "/api/close", {"position_id": p["position_id"]}, a.token)[0]
        == 200
    )
    assert a.store.all("position")[0]["status"] == "CLOSE_PENDING"
    assert request(base, "/api/demo-step", {}, a.token)[0] == 200
    assert a.store.all("position")[0]["status"] == "CLOSED"
    assert a.engine.reconcile(a.now())["status"] == "OK"
    status, body = request(base, "/api/export")
    assert status == 200 and json.loads(body)["non_executable"] is True


def test_stored_text_not_inlined_into_html(api):
    a, base = api
    dangerous = "<img src=x onerror=alert(1)>"
    request(base, "/api/settings", {"note": dangerous}, a.token)
    status, body = request(base, "/")
    assert status == 200 and dangerous.encode() not in body
    assert json.loads(request(base, "/api/state")[1])["draft"]["note"] == dangerous
