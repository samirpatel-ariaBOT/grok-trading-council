import sqlite3
from decimal import Decimal
import pytest
from services.core import DomainError, canonical
from services.data.adapters import instruments, candles
from services.data.scanner import scan
from services.features.baseline import propose, plan_prices, regime
from services.coordinator.store import Store
from services.fixtures import packet, case, report, at, quote, prepare_decision, NOW
from services.paper.engine import PaperEngine
from research.evaluation import metrics


def setup(tmp_path):
    s = Store(tmp_path / "ledger.sqlite")
    e = PaperEngine(s)
    e.initialize_demo(at(0))
    e.monitor({}, NOW)
    prepare_decision(s)
    return s, e


def test_numeric_collapse_finite_and_risk_rounding(tmp_path):
    for x in (True, False, float("nan"), float("inf"), 0, -1):
        assert plan_prices("UPTREND", "LONG", 1, x, x, "0.01")["status"] == "NO_SETUP"
    s, e = setup(tmp_path)
    o = e.admit("CASE-DEMO-001", "r1", quote(), NOW)
    assert Decimal(o["reserved_risk"]) <= 25
    assert Decimal(o["reserved_notional"]) <= 1500
    assert Decimal(o["qty"]) % Decimal("0.01") == 0


def test_regime_uses_seeded_values_numerically():
    # Independent oracle for an arithmetic progression: SMA seed puts the EMA
    # exactly (period-1)/2 steps behind, and every subsequent step preserves it.
    result = regime(packet()["hourly"], at(1))
    assert abs(Decimal(result["ema50"]) - Decimal("95.745")) < Decimal("1e-24")
    assert abs(Decimal(result["ema200"]) - Decimal("94.995")) < Decimal("1e-24")
    assert abs(Decimal(result["slope3"]) - Decimal("0.03")) < Decimal("1e-24")


def test_expiry_and_fresh_quote(tmp_path):
    p = packet()
    c = case()
    c["deadline"] = at(1000)
    result = propose(c, p, at(2))
    assert result["expires_at"] == at(122)
    s, e = setup(tmp_path)
    with pytest.raises(DomainError):
        e.admit("CASE-DEMO-001", "late", quote(), at(121))
    q = quote()
    q["source_at"] = at(3)
    with pytest.raises(DomainError, match="FUTURE"):
        e.admit("CASE-DEMO-001", "future", q, NOW)


def test_malformed_symbol_remains_strict_json():
    p = {
        "success": True,
        "code": 0,
        "data": [{"symbol": float("nan")}, "invalid", None],
    }
    result = scan(p, at(1))
    assert result["counts"] == {"raw": 3, "eligible": 0, "rejected": 3}
    assert "NaN" not in canonical(result)


def test_role_and_snapshot_mismatch(tmp_path):
    s = Store(tmp_path / "s.sqlite")
    c = case()
    s.create_case(c, packet(), at(1))
    r = report(c, "news")
    r["bot_id"] = report(c, "chief")["bot_id"]
    with pytest.raises(DomainError, match="BOT_ID"):
        s.import_report(r, "tester", at(1.5))
    r = report(c, "news")
    r["snapshot_id"] = "wrong"
    with pytest.raises(DomainError, match="snapshot_id"):
        s.import_report(r, "tester", at(1.5))
    r = report(c, "news")
    r["provenance"][0]["available_at"] = at(3)
    with pytest.raises(DomainError, match="EVIDENCE_AFTER"):
        s.import_report(r, "tester", at(1.5))
    r = report(c, "auditor")
    with pytest.raises(DomainError, match="AUDITOR_OUTSIDE"):
        s.import_report(r, "tester", at(1.5))


def test_unauthorized_real_packet_cannot_fill(tmp_path):
    s, e = setup(tmp_path)
    with s.transaction() as db:
        snap = s.get("snapshot", "SNAP-CASE-DEMO-001", db)
        snap["fictional"] = False
        s.put(db, "snapshot", snap["snapshot_id"], snap, replace=True)
    with pytest.raises(DomainError, match="NON_FIXTURE"):
        e.admit("CASE-DEMO-001", "r", quote(), NOW)


def test_corrupt_cash_and_backup_recovery(tmp_path):
    s, e = setup(tmp_path)
    o = e.admit("CASE-DEMO-001", "r", quote(), NOW)
    e.fill_entry(o["order_id"], "f", "1", quote(), NOW)
    backup = tmp_path / "backup.sqlite"
    with s.connect() as src, sqlite3.connect(backup) as dst:
        src.backup(dst)
    assert PaperEngine(Store(backup)).reconcile(NOW)["status"] == "OK"
    with s.transaction() as db:
        a = s.get("account", "DEMO", db)
        a["cash"] = "999999"
        s.put(db, "account", "DEMO", a, replace=True)
    assert e.reconcile(NOW) == {"status": "BLOCKED", "problems": ["CASH_MISMATCH"]}
    assert "CASH_MISMATCH" in PaperEngine(Store(s.path)).summary()["latched_reasons"]


def test_daily_unrealized_loss_latches_and_survives_restart(tmp_path):
    s, e = setup(tmp_path)
    o = e.admit("CASE-DEMO-001", "r", quote(), NOW)
    e.fill_entry(o["order_id"], "f", o["qty"], quote(), NOW)
    e.monitor({"DEMO_USDT": quote("80", at(3))}, at(3))
    assert "DAILY_LOSS_LIMIT" in PaperEngine(Store(s.path)).summary()["latched_reasons"]
    assert s.all("position")[0]["status"] == "CLOSE_PENDING"


def test_duplicate_trigger_not_retraded(tmp_path):
    s, e = setup(tmp_path)
    o = e.admit("CASE-DEMO-001", "r", quote(), NOW)
    e.fill_entry(o["order_id"], "f", "1", quote(), NOW)
    p = s.all("position")[0]
    e.request_close(p["position_id"], NOW)
    e.fill_exit(p["position_id"], "x", "1", quote(), NOW)
    prepare_decision(s, "CASE-REPLAY")
    with pytest.raises(DomainError, match="TRIGGER_ALREADY"):
        e.admit("CASE-REPLAY", "r2", quote(), NOW)


def test_metadata_and_actual_candle_availability():
    raw = {
        "success": True,
        "code": 0,
        "data": [
            {
                "symbol": "BTC_USDT",
                "baseCoin": "BTC",
                "quoteCoin": "USDT",
                "settleCoin": "USDT",
                "state": 0,
                "automaticDelivery": 0,
                "contractSize": "0.0001",
                "priceUnit": "0.1",
                "volUnit": "1",
                "minVol": "1",
                "maxVol": "1000",
            }
        ],
    }
    parsed = instruments(raw)[0]
    assert parsed["family"] == "UNVERIFIED" and parsed["allowed_sides"] == []
    raw["data"][0]["state"] = True
    with pytest.raises(DomainError):
        instruments(raw)
    candles_raw = {
        "success": True,
        "code": 0,
        "data": {
            "time": [1793706300],
            "open": [100],
            "high": [101],
            "low": [99],
            "close": [100],
            "vol": [1],
        },
    }
    result = candles(candles_raw, 900, at(2))
    assert result[0]["available_at"] == at(2)
    candles_raw["data"]["low"] = []
    with pytest.raises(DomainError, match="ARRAY_LENGTH"):
        candles(candles_raw, 900, at(2))


def test_metrics_independent_arithmetic():
    m = metrics(["10", "-5", "4"], ["100", "110", "99", "108"])
    assert m["expectancy"] == "3" and m["profit_factor"] == "2.8"
    assert m["maximum_drawdown_fraction"] == "0.1" and m["activation"] is False
    assert metrics(["1"], ["100", "101"])["profit_factor"] is None
    assert metrics([], [])["status"] == "NOT_MEASURED"
