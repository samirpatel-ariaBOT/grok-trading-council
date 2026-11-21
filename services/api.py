"""Loopback DEMO application. Public trading/data credentials are never accepted."""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from datetime import timedelta
import mimetypes
import secrets
import uuid
from urllib.parse import urlparse
from services.core import DomainError, canonical, strict_loads, iso, utc
from services.fixtures import seed, quote, report
from services.coordinator.contracts import ROSTER

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "apps/dashboard"


class Application:
    def __init__(self, path):
        self.store, self.engine = seed(path)
        self.token = secrets.token_urlsafe(32)
        self.engine.reconcile(self.now())

    def now(self):
        return self.store.get("clock", "DEMO")["at"]

    def state(self):
        cases = self.store.all("case")
        decisions = self.store.all("decision")
        return {
            "project": "Grok Trading Council",
            "version": "0.2.0",
            "mode": "DEMO",
            "stage": "IN_PROGRESS",
            "fixture_clock": self.now(),
            "live_market_connected": False,
            "native_operations": strict_loads(
                (ROOT / "config/native_operations.json").read_text()
            ),
            "account": self.engine.summary(),
            "cases": cases,
            "decisions": decisions,
            "reports": self.store.all("report"),
            "events": self.store.events(),
            "roster": [
                {
                    "role": role,
                    "bot_id": identity,
                    "native_status": "UNVERIFIED",
                    "instruction_version": "spec-v2; account application unverified",
                }
                for role, identity in ROSTER.items()
            ],
            "draft": self.store.get("draft", "policy"),
            "experiments": self.store.all("experiment"),
            "blockers": [
                "Native 24/7 schedules and unattended run evidence",
                "Native Sentiment sample and veto handoff",
                "Native group membership and automatic report delivery",
                "Operational instrument/policy/budget approval",
                "D: volume and durable runtime verification",
                "Out-of-sample and forward performance evidence",
            ],
            "market": [
                {
                    "symbol": "DEMO_USDT",
                    "name": "Fictional contract",
                    "price": "100.01",
                    "change": "+1.18%",
                    "spread": "1.00 bps",
                    "turnover": "Fixture only",
                    "regime": "UPTREND",
                    "eligible": "DEMO ONLY",
                    "points": [
                        99.1,
                        99.25,
                        99.2,
                        99.4,
                        99.35,
                        99.5,
                        99.4,
                        99.65,
                        99.6,
                        99.7,
                        99.62,
                        99.8,
                        99.72,
                        99.85,
                        99.8,
                        99.9,
                        99.82,
                        99.95,
                        100,
                        100.01,
                    ],
                }
            ],
        }

    def action(self, path, data):
        now = self.now()
        if path == "/api/import":
            if set(data) != {"report", "operator"}:
                raise DomainError("INVALID_IMPORT_ENVELOPE")
            return self.store.import_report(data["report"], data["operator"], now)
        if path == "/api/release":
            return self.store.release(data["case_id"], now)
        if path == "/api/decide":
            return self.store.decide(data["case_id"], now)
        if path == "/api/case":
            # Immutable new packet; editing source context is not supported here.
            source = self.store.get("case", data["source_case_id"])
            if source["status"] != "DECIDED":
                raise DomainError("SOURCE_CASE_NOT_CLOSED")
            new_id = f"CASE-DEMO-{uuid.uuid4().hex[:10]}"
            c = {
                k: source[k]
                for k in (
                    "snapshot_id",
                    "strategy_version",
                    "policy_version",
                    "data_cutoff",
                    "deadline",
                    "symbol",
                    "fixture",
                )
            }
            c["case_id"] = new_id
            snap = self.store.get("snapshot", source["snapshot_id"])
            self.store.create_case(c, snap, now)
            return self.store.get("case", new_id)
        if path == "/api/pause":
            return self.engine.pause(now)
        if path == "/api/close":
            return self.engine.request_close(data["position_id"], now)
        if path == "/api/demo-step":
            next_at = iso(utc(now) + timedelta(seconds=1))
            q = quote("100", next_at)
            self.engine.monitor({"DEMO_USDT": q}, next_at)
            # Explicit step fills pending fixture exits only. There is no live broker.
            for p in self.store.all("position"):
                if p["status"] == "CLOSE_PENDING":
                    self.engine.fill_exit(
                        p["position_id"], f"FILL-{uuid.uuid4()}", p["qty"], q, next_at
                    )
            with self.store.transaction() as db:
                self.store.put(
                    db,
                    "clock",
                    "DEMO",
                    {"at": next_at, "kind": "FROZEN_FICTIONAL_CLOCK"},
                    replace=True,
                )
            return {"fixture_clock": next_at}
        if path == "/api/experiment":
            name = data.get("name")
            hypothesis = data.get("hypothesis")
            if (
                not isinstance(name, str)
                or not 1 <= len(name.strip()) <= 100
                or not isinstance(hypothesis, str)
                or not 1 <= len(hypothesis.strip()) <= 2000
            ):
                raise DomainError("EXPERIMENT_FIELDS_REQUIRED")
            item = {
                "experiment_id": f"EXP-{uuid.uuid4().hex[:8]}",
                "name": name,
                "hypothesis": hypothesis,
                "status": "DRAFT",
                "evaluation": "NOT_MEASURED",
                "activation": False,
                "created_at": now,
            }
            with self.store.transaction() as db:
                self.store.put(db, "experiment", item["experiment_id"], item)
                self.store.event(
                    db, "EXPERIMENT_DRAFTED", item["experiment_id"], item, now
                )
            return item
        if path == "/api/settings":
            if (
                set(data) != {"note"}
                or not isinstance(data["note"], str)
                or len(data["note"]) > 2000
            ):
                raise DomainError("INVALID_DRAFT")
            with self.store.transaction() as db:
                item = self.store.get("draft", "policy", db)
                item.update(note=data["note"], status="UNAPPROVED")
                self.store.put(db, "draft", "policy", item, replace=True)
                self.store.event(
                    db, "POLICY_DRAFT_SAVED", "DEMO", {"status": "UNAPPROVED"}, now
                )
            return item
        raise DomainError("UNSUPPORTED_ACTION")


def server(app, port=8765, *, preview=False):
    class Handler(BaseHTTPRequestHandler):
        server_version = "GTC-Local-Demo/0.2"

        def log_message(self, *args):
            pass

        def permitted_host(self):
            host = self.headers.get("Host", "").split(":")[0]
            return preview or host in ("127.0.0.1", "localhost")

        def send(self, status, body, content_type="application/json; charset=utf-8"):
            if not isinstance(body, bytes):
                body = canonical(body).encode()
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header(
                "Content-Security-Policy",
                "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'",
            )
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if not self.permitted_host():
                return self.send(403, {"error": "HOST_REJECTED"})
            path = urlparse(self.path).path
            try:
                if path == "/api/session":
                    return self.send(200, {"token": app.token, "mode": "DEMO"})
                if path == "/api/state":
                    return self.send(200, app.state())
                if path == "/api/export":
                    return self.send(
                        200,
                        {
                            "mode": "DEMO",
                            "events": app.store.events(),
                            "cases": app.store.all("case"),
                            "reports": app.store.all("report"),
                            "decisions": app.store.all("decision"),
                            "non_executable": True,
                        },
                    )
                if path.startswith("/api/sample/"):
                    c = app.store.get("case", path.split("/")[-1])
                    return self.send(200, report(c, "news"))
                files = {
                    "/": "index.html",
                    "/index.html": "index.html",
                    "/app.js": "app.js",
                    "/style.css": "style.css",
                    "/favicon.svg": "favicon.svg",
                }
                if path not in files:
                    return self.send(404, {"error": "NOT_FOUND"})
                file = ASSETS / files[path]
                return self.send(
                    200,
                    file.read_bytes(),
                    mimetypes.guess_type(file)[0] + "; charset=utf-8",
                )
            except DomainError as exc:
                return self.send(400, {"error": exc.code, "detail": exc.detail})

        def do_POST(self):
            if not self.permitted_host() or not secrets.compare_digest(
                self.headers.get("X-GTC-Token", ""), app.token
            ):
                return self.send(403, {"error": "SESSION_REQUIRED"})
            origin = self.headers.get("Origin")
            if (
                origin
                and urlparse(origin).netloc != self.headers.get("Host")
                and not (
                    preview and self.headers.get("Sec-Fetch-Site") == "same-origin"
                )
            ):
                return self.send(403, {"error": "ORIGIN_REJECTED"})
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if not 0 < size <= 262144:
                    raise DomainError("INVALID_BODY_SIZE")
                data = strict_loads(self.rfile.read(size).decode("utf-8"))
                if not isinstance(data, dict):
                    raise DomainError("OBJECT_REQUIRED")
                result = app.action(urlparse(self.path).path, data)
                return self.send(200, {"result": result})
            except DomainError as exc:
                return self.send(400, {"error": exc.code, "detail": exc.detail})
            except (KeyError, ValueError, TypeError, UnicodeDecodeError):
                return self.send(400, {"error": "MALFORMED_REQUEST"})

    return ThreadingHTTPServer(("0.0.0.0" if preview else "127.0.0.1", port), Handler)
