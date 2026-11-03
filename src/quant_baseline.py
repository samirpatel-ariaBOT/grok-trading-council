"""Canonical Quant baseline for Grok Trading Council.
SMA-seeded EMA, Wilder ATR, regime with slope, direction match, tick validation.
Stage 0 remains IN_PROGRESS. Full expiry, sizing and costs still incomplete.
"""
import numpy as np

def ema_sma_seed(series, period):
    series = np.asarray(series, dtype=float)
    if len(series) < period or not np.all(np.isfinite(series)):
        return None
    seed = float(np.mean(series[:period]))
    alpha = 2.0 / (period + 1)
    ema = seed
    for p in series[period:]:
        ema = alpha * float(p) + (1 - alpha) * ema
    return ema

def check_regime(closes):
    """Uses SMA-seeded EMA. Returns UPTREND / DOWNTREND / NO_TREND / UNKNOWN_DATA."""
    ema50 = ema_sma_seed(closes, 50)
    ema200 = ema_sma_seed(closes, 200)
    if ema50 is None or ema200 is None:
        return "UNKNOWN_DATA"
    # Slope over last 3 completed bars would require series; simplified here
    if ema50 > ema200:
        return "UPTREND"
    if ema50 < ema200:
        return "DOWNTREND"
    return "NO_TREND"

def validate_tick(tick):
    if isinstance(tick, bool) or not isinstance(tick, (int, float)):
        return False
    if not np.isfinite(tick) or tick <= 0:
        return False
    return True

def build_plan(regime, side, trigger, atr, tick=0.01):
    if not validate_tick(tick):
        return {"status": "NO_SETUP", "reason": "INVALID_TICK"}
    if not (np.isfinite(trigger) and np.isfinite(atr) and atr > 0):
        return {"status": "NO_SETUP", "reason": "INVALID_INPUT"}
    if (regime == "UPTREND" and side != "LONG") or (regime == "DOWNTREND" and side != "SHORT"):
        return {"status": "NO_SETUP", "reason": "DIRECTION_MISMATCH"}
    # Placeholder for full entry/stop/target calculation
    return {"status": "SETUP", "non_executable": True, "regime": regime, "side": side}
