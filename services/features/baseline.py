"""Canonical v2 p19/35 baseline. Decimal precision 28; outputs cannot execute."""

from __future__ import annotations
from datetime import timedelta
from decimal import Decimal
from typing import Any
from services.core import (
    DomainError,
    decimal_value as num,
    ds,
    epoch,
    fresh_quote,
    iso,
    tick_round,
    utc,
)

VERSION = "baseline-v1"


def completed_bars(
    rows: list[dict], interval: int, cutoff: str, minimum: int
) -> list[dict]:
    if interval not in (900, 3600) or not isinstance(rows, list):
        raise DomainError("INVALID_HISTORY")
    end, completed, last = epoch(cutoff), [], None
    for row in rows:
        start, close, available = (
            epoch(row["open_at"]),
            epoch(row["close_at"]),
            epoch(row["available_at"]),
        )
        if start % interval or close != start + interval or available < close:
            raise DomainError("BAR_ALIGNMENT")
        if last is not None and start <= last:
            raise DomainError("DUPLICATE_OR_UNORDERED_BAR")
        last = start
        values = {
            key: num(row[key], nonnegative=key == "volume", positive=key != "volume")
            for key in ("open", "high", "low", "close", "volume")
        }
        if (
            not values["low"]
            <= min(values["open"], values["close"])
            <= max(values["open"], values["close"])
            <= values["high"]
        ):
            raise DomainError("INVALID_OHLC")
        if close < end and available < end:
            completed.append({**row, **values})
    if len(completed) < minimum:
        raise DomainError("INSUFFICIENT_HISTORY")
    for previous, current in zip(completed, completed[1:]):
        if epoch(current["open_at"]) != epoch(previous["close_at"]):
            raise DomainError("HISTORY_GAP")
    if end - epoch(completed[-1]["close_at"]) > interval:
        raise DomainError("HISTORY_STALE")
    return completed


def ema(values: list[Any], period: int) -> list[Decimal | None]:
    if type(period) is not int or period <= 0:
        raise DomainError("INVALID_PERIOD")
    data = [num(v, positive=True) for v in values]
    if len(data) < period:
        raise DomainError("INSUFFICIENT_HISTORY")
    result: list[Decimal | None] = [None] * (period - 1)
    value = sum(data[:period], Decimal(0)) / period
    result.append(value)
    alpha = Decimal(2) / (period + 1)
    for point in data[period:]:
        value = alpha * point + (1 - alpha) * value
        result.append(value)
    return result


def atr(bars: list[dict], period: int = 14) -> Decimal:
    if type(period) is not int or period <= 0 or len(bars) < period:
        raise DomainError("INSUFFICIENT_HISTORY")
    ranges, previous = [], None
    for bar in bars:
        high, low, close = (
            num(bar[k], positive=True) for k in ("high", "low", "close")
        )
        if not low <= close <= high:
            raise DomainError("INVALID_OHLC")
        ranges.append(
            high - low
            if previous is None
            else max(high - low, abs(high - previous), abs(low - previous))
        )
        previous = close
    value = sum(ranges[:period], Decimal(0)) / period
    for item in ranges[period:]:
        value = ((period - 1) * value + item) / period
    if value <= 0:
        raise DomainError("INVALID_ATR")
    return value


def regime(rows: list[dict], cutoff: str) -> dict:
    try:
        bars = completed_bars(rows, 3600, cutoff, 600)
        fast, slow = (
            ema([b["close"] for b in bars], 50),
            ema([b["close"] for b in bars], 200),
        )
        delta = fast[-1] - fast[-4]
        state = (
            "UPTREND"
            if fast[-1] > slow[-1] and delta > 0
            else "DOWNTREND"
            if fast[-1] < slow[-1] and delta < 0
            else "NO_TREND"
        )
        return {
            "state": state,
            "ema50": ds(fast[-1]),
            "ema200": ds(slow[-1]),
            "slope3": ds(delta),
            "history_anchor": bars[0]["open_at"],
            "bar_count": len(bars),
        }
    except (DomainError, KeyError, TypeError) as exc:
        return {
            "state": "UNKNOWN_DATA",
            "reason": getattr(exc, "code", "INVALID_HISTORY"),
        }


def trigger(rows: list[dict], cutoff: str, side: str) -> dict:
    try:
        if side not in ("LONG", "SHORT"):
            raise DomainError("UNSUPPORTED_SIDE")
        bars = completed_bars(rows, 900, cutoff, 21)
        prior, current = bars[-21:-1], bars[-1]
        mean = sum((b["volume"] for b in prior), Decimal(0)) / 20
        if mean <= 0 or current["volume"] <= Decimal("1.5") * mean:
            raise DomainError("VOLUME_NOT_CONFIRMED")
        threshold = (
            max(b["high"] for b in prior)
            if side == "LONG"
            else min(b["low"] for b in prior)
        )
        if not (
            current["close"] > threshold
            if side == "LONG"
            else current["close"] < threshold
        ):
            raise DomainError("NO_BREAKOUT")
        return {
            "status": "BREAKOUT",
            "side": side,
            "trigger_close": ds(current["close"]),
            "trigger_at": current["close_at"],
            "available_at": current["available_at"],
            "atr_frozen": ds(atr(bars)),
            "setup_expires_at": iso(utc(current["close_at"]) + timedelta(seconds=900)),
            "history_anchor": bars[0]["open_at"],
        }
    except (DomainError, KeyError, TypeError) as exc:
        return {"status": "NO_SETUP", "reason": getattr(exc, "code", "INVALID_HISTORY")}


def plan_prices(
    state: str,
    breakout_side: str,
    frozen_atr: Any,
    trigger_close: Any,
    entry_quote: Any,
    tick: Any,
) -> dict:
    try:
        if state not in ("UPTREND", "DOWNTREND"):
            raise DomainError("NO_PERMITTED_REGIME")
        side = "LONG" if state == "UPTREND" else "SHORT"
        if breakout_side != side:
            raise DomainError("DIRECTION_MISMATCH")
        step = num(tick, positive=True)
        a, c, q = [
            num(v, positive=True) for v in (frozen_atr, trigger_close, entry_quote)
        ]
        entry = tick_round(q, step, up=side == "LONG")
        if abs(q - c) > a / 4 or abs(entry - c) > a / 4:
            raise DomainError("ENTRY_DRIFT")
        stop = tick_round(
            entry + (-1 if side == "LONG" else 1) * Decimal("1.5") * a,
            step,
            up=side == "SHORT",
        )
        target = tick_round(
            entry + (1 if side == "LONG" else -1) * 3 * a, step, up=side == "SHORT"
        )
        ordered = (
            0 < stop < entry < target if side == "LONG" else 0 < target < entry < stop
        )
        if not ordered:
            raise DomainError("INVALID_ROUNDED_PRICES")
        return {
            "status": "PLAN",
            "side": side,
            "entry": ds(entry),
            "stop": ds(stop),
            "target": ds(target),
            "atr_frozen": ds(a),
            "entry_min": ds(max(step, c - a / 4)),
            "entry_max": ds(c + a / 4),
            "trigger_close": ds(c),
            "tick_size": ds(step),
            "max_hold_seconds": 14400,
            "non_executable": True,
        }
    except (DomainError, TypeError, ValueError) as exc:
        return {"status": "NO_SETUP", "reason": getattr(exc, "code", "INVALID_INPUT")}


def propose(case: dict, snapshot: dict, decision_at: str) -> dict:
    """Recompute from the frozen packet; a bot cannot supply authoritative prices."""
    try:
        now = utc(decision_at)
        if now < utc(case["data_cutoff"]) or now >= utc(case["deadline"]):
            raise DomainError("CASE_EXPIRED")
        r = regime(snapshot["hourly"], case["data_cutoff"])
        if r["state"] not in ("UPTREND", "DOWNTREND"):
            raise DomainError(r.get("reason", "NO_PERMITTED_REGIME"))
        side = "LONG" if r["state"] == "UPTREND" else "SHORT"
        b = trigger(snapshot["candles"], case["data_cutoff"], side)
        if b["status"] != "BREAKOUT":
            raise DomainError(b["reason"])
        metadata = snapshot["instrument"]
        if (
            metadata["family"] != "LINEAR_PERPETUAL"
            or metadata["active"] is not True
            or side not in metadata["allowed_sides"]
        ):
            raise DomainError("UNSUPPORTED_INSTRUMENT")
        for key in ("contract_size", "tick_size", "qty_step", "min_qty", "max_qty"):
            num(metadata[key], positive=True)
        expiry = min(
            utc(b["setup_expires_at"]),
            now + timedelta(seconds=120),
            utc(case["deadline"]),
        )
        if now >= expiry or now <= utc(b["available_at"]):
            raise DomainError("SETUP_EXPIRED")
        bid, ask = fresh_quote(snapshot["quote"], decision_at)
        p = plan_prices(
            r["state"],
            side,
            b["atr_frozen"],
            b["trigger_close"],
            ask if side == "LONG" else bid,
            metadata["tick_size"],
        )
        if p["status"] != "PLAN":
            return p
        return {
            **p,
            "plan_id": f"PLAN-{case['case_id']}-1",
            "plan_version": 1,
            "case_id": case["case_id"],
            "snapshot_id": case["snapshot_id"],
            "symbol": metadata["symbol"],
            "venue": "MEXC",
            "strategy_version": VERSION,
            "policy_version": case["policy_version"],
            "created_at": decision_at,
            "expires_at": iso(expiry),
            "setup_expires_at": b["setup_expires_at"],
            "trigger_at": b["trigger_at"],
            "trigger_key": f"MEXC:{metadata['symbol']}:15m:{b['trigger_at']}:{VERSION}",
            "contract_size": metadata["contract_size"],
            "quantity_unit": "contracts",
            "order_type": "PAPER_MARKET",
            "regime": r,
            "costs": snapshot["costs"],
        }
    except (DomainError, KeyError, TypeError) as exc:
        return {
            "status": "NO_SETUP",
            "reason": getattr(exc, "code", "INVALID_SNAPSHOT"),
        }
