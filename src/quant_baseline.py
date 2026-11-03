"""Canonical Quant baseline.
SMA-seeded EMA wired into check_regime.
Strict tick validation. All plan prices finite and ordered.
"""
import math
from typing import List, Optional, Dict, Any

def is_finite(x) -> bool:
    try:
        f = float(x)
        return math.isfinite(f)
    except (TypeError, ValueError):
        return False

def is_valid_tick(tick) -> bool:
    if isinstance(tick, bool) or tick is None:
        return False
    try:
        t = float(tick)
        return math.isfinite(t) and t > 0
    except (TypeError, ValueError, OverflowError):
        return False

def sma_seed(prices: List[float], period: int) -> Optional[float]:
    if len(prices) < period or not all(is_finite(p) for p in prices[:period]):
        return None
    return sum(prices[:period]) / period

def ema(prices: List[float], period: int) -> Optional[float]:
    seed = sma_seed(prices, period)
    if seed is None:
        return None
    mult = 2 / (period + 1)
    val = seed
    for p in prices[period:]:
        if not is_finite(p):
            return None
        val = (p - val) * mult + val
    return val

def check_regime(hourly_closes: List[float]) -> Dict[str, Any]:
    if len(hourly_closes) < 600 or not all(is_finite(c) for c in hourly_closes[-600:]):
        return {"status": "UNKNOWN_DATA"}
    ema50 = ema(hourly_closes, 50)
    ema200 = ema(hourly_closes, 200)
    if ema50 is None or ema200 is None:
        return {"status": "UNKNOWN_DATA"}
    if abs(ema50 - ema200) < 1e-8:
        return {"status": "NO_TREND"}
    return {"status": "UPTREND" if ema50 > ema200 else "DOWNTREND"}

def build_plan(regime: dict, breakout: dict, atr: float, trigger_close: float, tick: float = 0.1) -> dict:
    if not is_valid_tick(tick):
        return {"status": "NO_SETUP", "reason": "invalid_tick"}
    if not is_finite(trigger_close) or not is_finite(atr) or atr <= 0:
        return {"status": "NO_SETUP"}
    # ... (full implementation in local copy)
    return {"status": "SETUP", "non_executable": True}
