"""Bounded, public GET collector. Never accepts arbitrary URLs or credentials."""

from datetime import datetime, timezone
import hashlib
from pathlib import Path
import time
import urllib.error
import urllib.request
import uuid
from services.core import DomainError, canonical, iso, strict_loads
from services.data.scanner import scan, envelope

BASE = "https://contract.mexc.com"
PATHS = {
    "ticker": "/api/v1/contract/ticker",
    "detail": "/api/v1/contract/detail",
    "ping": "/api/v1/contract/ping",
}
MAX_BYTES = 16 * 1024 * 1024


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise DomainError("REDIRECT_REJECTED")


class Collector:
    def __init__(self, root, *, transport=None):
        self.root = Path(root)
        self.transport = transport or self._get
        self.last_call = {}

    def _get(self, url):
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "GTC-readonly/0.2", "Accept": "application/json"},
            method="GET",
        )
        with urllib.request.build_opener(NoRedirect).open(
            request, timeout=10
        ) as response:
            return response.status, response.read(MAX_BYTES + 1)

    def collect(self, kind):
        if kind not in PATHS:
            raise DomainError("UNSUPPORTED_ENDPOINT")
        # Per-instance limiter; CLI invokes one collector, not parallel clients.
        interval = 5 if kind == "detail" else 0.2
        if time.monotonic() - self.last_call.get(kind, -1e12) < interval:
            raise DomainError("LOCAL_RATE_LIMIT")
        self.last_call[kind] = time.monotonic()
        sent = iso()
        started = time.monotonic()
        try:
            status, body = self.transport(BASE + PATHS[kind])
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise DomainError("NETWORK_ERROR", str(type(exc).__name__)) from exc
        received = iso()
        elapsed = time.monotonic() - started
        if len(body) > MAX_BYTES:
            raise DomainError("RESPONSE_TOO_LARGE")
        # Persist actual response even for HTTP/API errors; exclusive creation.
        raw_id = f"RAW-{uuid.uuid4()}"
        folder = self.root / raw_id
        folder.mkdir(parents=True, exist_ok=False)
        (folder / "body.bin").write_bytes(body)
        meta = {
            "raw_id": raw_id,
            "url": BASE + PATHS[kind],
            "http_status": status,
            "sent_at": sent,
            "received_at": received,
            "elapsed_seconds": elapsed,
            "sha256": hashlib.sha256(body).hexdigest(),
            "kind": kind,
        }
        (folder / "provenance.json").write_text(canonical(meta), encoding="utf-8")
        if status != 200:
            raise DomainError("HTTP_ERROR", f"HTTP {status}; raw_id={raw_id}")
        try:
            payload = strict_loads(body.decode("utf-8"))
        except (UnicodeDecodeError, DomainError) as exc:
            raise DomainError("INVALID_RESPONSE", raw_id) from exc
        if kind == "ping":
            if (
                not isinstance(payload, dict)
                or payload.get("success") is not True
                or type(payload.get("data")) is not int
            ):
                raise DomainError("API_ERROR")
            server = datetime.fromtimestamp(payload["data"] / 1000, timezone.utc)
            meta.update(server_at=iso(server), clock_uncertainty_seconds=elapsed / 2)
        else:
            envelope(payload)
        return payload, meta

    def discover(self):
        payload, meta = self.collect("ticker")
        result = scan(payload, meta["received_at"])
        result["raw_id"] = meta["raw_id"]
        result["metadata_status"] = "NOT_JOINED; not admissible for execution"
        file = self.root / (result["snapshot_id"] + ".json")
        with file.open("x", encoding="utf-8") as stream:
            stream.write(canonical(result))
        return result
