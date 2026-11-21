"""Normalize public metadata/OHLC arrays, preserving unresolved eligibility."""

from datetime import datetime, timezone, timedelta
from services.core import DomainError, decimal_value as n, ds, iso, utc
from services.data.scanner import envelope, SYMBOL


def instruments(payload):
    rows = envelope(payload)
    if not isinstance(rows, list):
        raise DomainError("MALFORMED_METADATA")
    result = []
    seen = set()
    for row in rows:
        if (
            not isinstance(row, dict)
            or not isinstance(row.get("symbol"), str)
            or not SYMBOL.fullmatch(row["symbol"])
        ):
            raise DomainError("INVALID_SYMBOL")
        if row["symbol"] in seen:
            raise DomainError("DUPLICATE_SYMBOL")
        seen.add(row["symbol"])
        for k in ("state", "automaticDelivery"):
            if type(row.get(k)) is not int:
                raise DomainError("INVALID_METADATA_STATE")
        if not all(
            isinstance(row.get(k), str) and row[k]
            for k in ("baseCoin", "quoteCoin", "settleCoin")
        ):
            raise DomainError("MISSING_SETTLEMENT_METADATA")
        numeric = {
            out: ds(n(row.get(src), positive=True))
            for out, src in {
                "contract_size": "contractSize",
                "tick_size": "priceUnit",
                "qty_step": "volUnit",
                "min_qty": "minVol",
                "max_qty": "maxVol",
            }.items()
        }
        if n(numeric["min_qty"]) > n(numeric["max_qty"]) or n(numeric["min_qty"]) % n(
            numeric["qty_step"]
        ):
            raise DomainError("INVALID_QUANTITY_RULES")
        result.append(
            {
                "symbol": row["symbol"],
                "base": row["baseCoin"],
                "quote": row["quoteCoin"],
                "settlement": row["settleCoin"],
                "active": row["state"] == 0,
                "automatic_delivery": row["automaticDelivery"],
                "family": "UNVERIFIED",
                "allowed_sides": [],
                **numeric,
                "eligibility": "METADATA_ONLY; owner instrument-family and product scope unresolved",
            }
        )
    return result


def candles(payload, interval, received_at):
    if interval not in (900, 3600):
        raise DomainError("UNSUPPORTED_INTERVAL")
    data = envelope(payload)
    fields = ("time", "open", "high", "low", "close", "vol")
    if not isinstance(data, dict) or any(
        not isinstance(data.get(k), list) for k in fields
    ):
        raise DomainError("MALFORMED_CANDLES")
    if len({len(data[k]) for k in fields}) != 1:
        raise DomainError("ARRAY_LENGTH_MISMATCH")
    received = utc(received_at)
    result = []
    previous = None
    for i, timestamp in enumerate(data["time"]):
        if type(timestamp) is not int or timestamp <= 0 or timestamp % interval:
            raise DomainError("BAR_ALIGNMENT")
        if previous is not None and timestamp != previous + interval:
            raise DomainError("HISTORY_GAP")
        previous = timestamp
        start = datetime.fromtimestamp(timestamp, timezone.utc)
        close = start + timedelta(seconds=interval)
        values = {
            k: ds(n(data[k][i], positive=True))
            for k in ("open", "high", "low", "close")
        }
        volume = ds(n(data["vol"][i], nonnegative=True))
        if (
            not n(values["low"])
            <= min(n(values["open"]), n(values["close"]))
            <= max(n(values["open"]), n(values["close"]))
            <= n(values["high"])
        ):
            raise DomainError("INVALID_OHLC")
        if close > received:
            continue
        result.append(
            {
                "open_at": iso(start),
                "close_at": iso(close),
                "available_at": received_at,
                **values,
                "volume": volume,
                "availability_basis": "ACTUALLY_RECEIVED_NOW; not historical availability",
            }
        )
    return result
