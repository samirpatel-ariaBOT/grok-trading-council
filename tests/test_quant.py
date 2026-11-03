"""Cumulative regression tests for Quant baseline."""
import numpy as np
from src.quant_baseline import ema_sma_seed, check_regime, build_plan

def test_sma_seed():
    result = ema_sma_seed(np.array([1., 2., 3.]), 3)
    assert result == 2.0, f"Expected 2.0, got {result}"

def test_invalid_tick():
    result = build_plan("UPTREND", "LONG", 100, 1, tick=0)
    assert result["status"] == "NO_SETUP"
    result = build_plan("UPTREND", "LONG", 100, 1, tick=float("nan"))
    assert result["status"] == "NO_SETUP"

def test_direction_mismatch():
    result = build_plan("UPTREND", "SHORT", 100, 1)
    assert result["status"] == "NO_SETUP"

if __name__ == "__main__":
    test_sma_seed()
    test_invalid_tick()
    test_direction_mismatch()
    print("ALL TESTS PASSED")
