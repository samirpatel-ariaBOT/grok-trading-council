"""Strict values shared by GTC services. No network or trading side effects."""

from __future__ import annotations
import hashlib
import json
import re
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_CEILING, ROUND_FLOOR
from typing import Any


class DomainError(ValueError):
    def __init__(self, code: str, detail: str = ""):
        self.code, self.detail = code, detail or code
        super().__init__(self.detail)


def decimal_value(
    value: Any, *, positive: bool = False, nonnegative: bool = False
) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (str, int, float, Decimal)):
        raise DomainError("INVALID_NUMBER")
    if isinstance(value, str) and (
        len(value) > 80
        or not re.fullmatch(r"-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?", value)
    ):
        raise DomainError("INVALID_NUMBER")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError, OverflowError) as exc:
        raise DomainError("INVALID_NUMBER") from exc
    if (
        not result.is_finite()
        or abs(result) > Decimal("1e30")
        or (result != 0 and abs(result) < Decimal("1e-30"))
    ):
        raise DomainError("INVALID_NUMBER")
    if (positive and result <= 0) or (nonnegative and result < 0):
        raise DomainError("INVALID_NUMBER")
    return result


def ds(value: Decimal) -> str:
    return format(value, "f")


def utc(value: Any) -> datetime:
    if not isinstance(value, str) or not re.fullmatch(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z", value
    ):
        raise DomainError("INVALID_TIMESTAMP", "Use UTC RFC3339 ending in Z")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise DomainError("INVALID_TIMESTAMP") from exc
    if parsed.tzinfo is None or parsed.utcoffset().total_seconds() != 0:
        raise DomainError("INVALID_TIMESTAMP")
    return parsed


def iso(value: datetime | None = None) -> str:
    value = value or datetime.now(timezone.utc)
    if value.tzinfo is None:
        raise DomainError("INVALID_TIMESTAMP")
    return (
        value.astimezone(timezone.utc)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )


def epoch(value: Any) -> float:
    return utc(value).timestamp()


def canonical(value: Any) -> str:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    except (ValueError, TypeError, OverflowError) as exc:
        raise DomainError("INVALID_JSON") from exc


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def strict_loads(text: str) -> Any:
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise DomainError("DUPLICATE_PROPERTY", key)
            result[key] = value
        return result

    def invalid(_):
        raise DomainError("INVALID_NUMBER")

    try:
        value = json.loads(text, object_pairs_hook=pairs, parse_constant=invalid)
        canonical(value)
        return value
    except (json.JSONDecodeError, RecursionError) as exc:
        raise DomainError("INVALID_JSON") from exc


def tick_round(value: Decimal, tick: Decimal, *, up: bool) -> Decimal:
    return (value / tick).to_integral_value(
        rounding=ROUND_CEILING if up else ROUND_FLOOR
    ) * tick


def fresh_quote(
    quote: dict, now: str, max_age: float = 3, max_uncertainty: float = 1
) -> tuple[Decimal, Decimal]:
    bid, ask = (
        decimal_value(quote["bid"], positive=True),
        decimal_value(quote["ask"], positive=True),
    )
    if bid > ask:
        raise DomainError("CROSSED_BOOK")
    uncertainty = float(
        decimal_value(quote.get("clock_uncertainty_seconds"), nonnegative=True)
    )
    if uncertainty > max_uncertainty:
        raise DomainError("CLOCK_UNCERTAIN")
    source, received, current = (
        epoch(quote["source_at"]),
        epoch(quote["received_at"]),
        epoch(now),
    )
    if source > current or received > current or source > received + uncertainty:
        raise DomainError("FUTURE_TIMESTAMP")
    if max(current - source, current - received) + uncertainty > max_age:
        raise DomainError("DATA_STALE")
    return bid, ask
