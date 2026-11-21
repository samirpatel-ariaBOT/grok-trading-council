"""Lossless discovery: no candidate is a trade approval."""

from collections import Counter
from datetime import datetime, timezone
import re
import uuid
from services.core import DomainError, decimal_value as num, ds, digest, iso, epoch

SYMBOL = re.compile(r"[A-Z0-9]{1,32}_[A-Z0-9]{1,16}\Z")
POLICY = {
    "version": "discovery-v2",
    "quote": "USDT",
    "minimum_turnover": "100000",
    "maximum_spread_bps": "50",
    "maximum_age_seconds": 10,
}


def envelope(payload):
    if (
        not isinstance(payload, dict)
        or payload.get("success") is not True
        or type(payload.get("code")) is not int
        or payload["code"] != 0
    ):
        raise DomainError("API_ERROR")
    return payload.get("data")


def scan(
    payload,
    received_at,
    *,
    policy=None,
    http_status=200,
    source_url="https://contract.mexc.com/api/v1/contract/ticker",
):
    policy = dict(policy or POLICY)
    snapshot = {
        "snapshot_id": f"SCAN-{uuid.uuid4()}",
        "schema_version": "3.0",
        "policy": policy,
        "received_at": received_at,
        "source_url": source_url,
        "non_executable": True,
        "eligible": [],
        "rejected": [],
        "counts": {"raw": 0, "eligible": 0, "rejected": 0},
    }
    try:
        now = epoch(received_at)
        if type(http_status) is not int or http_status != 200:
            raise DomainError("HTTP_ERROR")
        rows = envelope(payload)
        if not isinstance(rows, list):
            raise DomainError("MALFORMED_DATA")
        symbols = Counter(
            row.get("symbol")
            for row in rows
            if isinstance(row, dict) and isinstance(row.get("symbol"), str)
        )
        snapshot["counts"]["raw"] = len(rows)
        # Raw HTTP bytes are hashed by the collector. Pure malformed-value fixtures
        # may be non-JSON Python objects: reject their rows without emitting NaN.
        try:
            snapshot["source_hash"] = digest(payload)
        except DomainError:
            snapshot["source_hash"] = None
            snapshot["source_hash_status"] = "INPUT_NOT_STRICT_JSON"
        for index, row in enumerate(rows):
            symbol = row.get("symbol") if isinstance(row, dict) else None
            safe_symbol = (
                symbol if isinstance(symbol, str) and len(symbol) <= 64 else None
            )
            try:
                if (
                    not isinstance(row, dict)
                    or not isinstance(symbol, str)
                    or not SYMBOL.fullmatch(symbol)
                ):
                    raise DomainError("INVALID_SYMBOL")
                if symbols[symbol] != 1:
                    raise DomainError("DUPLICATE_SYMBOL")
                if symbol.rsplit("_", 1)[1] != policy["quote"]:
                    raise DomainError("QUOTE_FILTER")
                last, bid, ask = [
                    num(row.get(k), positive=True)
                    for k in ("lastPrice", "bid1", "ask1")
                ]
                volume, turnover = [
                    num(row.get(k), nonnegative=True) for k in ("volume24", "amount24")
                ]
                stamp = num(row.get("timestamp"), positive=True)
                if stamp != stamp.to_integral_value():
                    raise DomainError("INVALID_TIMESTAMP")
                age = now - float(stamp) / 1000
                if age < 0:
                    raise DomainError("FUTURE_TIMESTAMP")
                if age > policy["maximum_age_seconds"]:
                    raise DomainError("DATA_STALE")
                if bid > ask:
                    raise DomainError("CROSSED_BOOK")
                spread = (ask - bid) / ((ask + bid) / 2) * 10000
                if turnover < num(policy["minimum_turnover"]):
                    raise DomainError("LOW_TURNOVER")
                if spread > num(policy["maximum_spread_bps"]):
                    raise DomainError("WIDE_SPREAD")
                snapshot["eligible"].append(
                    {
                        "symbol": symbol,
                        "last": ds(last),
                        "bid": ds(bid),
                        "ask": ds(ask),
                        "spread_bps": ds(spread),
                        "volume_contracts_24h": ds(volume),
                        "turnover_reported_24h": ds(turnover),
                        "turnover_unit": "exchange_amount24; verify settlement metadata",
                        "source_at": iso(
                            datetime.fromtimestamp(float(stamp) / 1000, timezone.utc)
                        ),
                        "received_at": received_at,
                        "eligibility": "DISCOVERY_ONLY",
                    }
                )
            except (DomainError, KeyError, TypeError, ValueError, OverflowError) as exc:
                snapshot["rejected"].append(
                    {
                        "row": index,
                        "symbol": safe_symbol,
                        "reason": getattr(exc, "code", "MALFORMED_ROW"),
                    }
                )
        snapshot["eligible"].sort(
            key=lambda row: num(row["turnover_reported_24h"]), reverse=True
        )
        snapshot["counts"].update(
            eligible=len(snapshot["eligible"]), rejected=len(snapshot["rejected"])
        )
        snapshot["status"] = "OK"
    except (DomainError, KeyError, TypeError) as exc:
        snapshot.update(status="ERROR", reason=getattr(exc, "code", "INVALID_INPUT"))
    return snapshot
