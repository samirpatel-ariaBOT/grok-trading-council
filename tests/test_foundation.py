import copy
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
import pytest
from services.core import DomainError, strict_loads, decimal_value
from services.features.baseline import ema, atr, regime, trigger, plan_prices, propose
from services.data.scanner import scan
from services.data.mexc import Collector
from services.coordinator.contracts import validate_report
from services.coordinator.store import Store
from services.paper.engine import PaperEngine
from services.fixtures import packet, case, report, at, quote, prepare_decision, NOW


@pytest.fixture
def system(tmp_path):
    store = Store(tmp_path / "test.sqlite")
    engine = PaperEngine(store)
    engine.initialize_demo(at(0))
    engine.monitor({}, NOW)
    prepare_decision(store)
    return store, engine


@pytest.mark.parametrize(
    "bad", [True, False, None, float("nan"), float("inf"), {}, [], "NaN", "1e1000"]
)
def test_bad_numbers(bad):
    with pytest.raises(DomainError):
        decimal_value(bad)


@pytest.mark.parametrize("raw", ['{"x":1,"x":2}', '{"n":NaN}', '{"n":1e400}'])
def test_strict_json(raw):
    with pytest.raises(DomainError):
        strict_loads(raw)


def test_sma_seed_and_wilder():
    values = ema([1, 2, 3, 10], 3)
    assert values == [None, None, Decimal(2), Decimal(6)]
    bars = [{"high": "3", "low": "1", "close": "2"} for _ in range(14)] + [
        {"high": "5", "low": "1", "close": "3"}
    ]
    assert atr(bars) == Decimal(30) / 14


def test_completed_regime_and_breakout():
    p = packet()
    c = case()
    assert regime(p["hourly"], c["data_cutoff"])["state"] == "UPTREND"
    assert trigger(p["candles"], c["data_cutoff"], "LONG")["status"] == "BREAKOUT"
    assert propose(c, p, at(2))["status"] == "PLAN"


@pytest.mark.parametrize(
    "kind",
    [
        "gap",
        "duplicate",
        "not_utc",
        "future",
        "nan",
        "bool",
        "invalid_ohlc",
        "short_history",
    ],
)
def test_invalid_history(kind):
    p = packet()
    rows = p["hourly"]
    if kind == "gap":
        del rows[50]
    if kind == "duplicate":
        rows[50] = copy.deepcopy(rows[49])
    if kind == "not_utc":
        rows[-1]["open_at"] = "2026-11-03T11:00:00"
    if kind == "future":
        rows[-1]["available_at"] = at(10)
    if kind == "nan":
        rows[-1]["close"] = float("nan")
    if kind == "bool":
        rows[-1]["close"] = True
    if kind == "invalid_ohlc":
        rows[-1]["low"] = "10000"
    if kind == "short_history":
        rows = rows[-200:]
    assert regime(rows, at(1))["state"] == "UNKNOWN_DATA"


def test_flat_regime():
    rows = packet()["hourly"]
    for r in rows:
        r.update(open="100", close="100", high="101", low="99")
    assert regime(rows, at(1))["state"] == "NO_TREND"


def test_breakout_excludes_trigger_and_uses_highs():
    rows = packet()["candles"]
    rows[-2]["high"] = "101"
    assert trigger(rows, at(1), "LONG")["reason"] == "NO_BREAKOUT"
    rows[-2]["high"] = "99.8"
    rows[-1]["volume"] = "150"
    assert trigger(rows, at(1), "LONG")["reason"] == "VOLUME_NOT_CONFIRMED"


@pytest.mark.parametrize(
    "tick", [True, False, 0, -1, None, float("nan"), float("inf"), "bad"]
)
def test_invalid_tick(tick):
    assert plan_prices("UPTREND", "LONG", 1, 100, 100, tick)["status"] == "NO_SETUP"


def test_plan_boundaries():
    assert (
        plan_prices("UPTREND", "SHORT", 1, 100, 100, 0.01)["reason"]
        == "DIRECTION_MISMATCH"
    )
    assert (
        plan_prices("UPTREND", "LONG", 1, 1, 1, 0.01)["reason"]
        == "INVALID_ROUNDED_PRICES"
    )
    assert plan_prices("UPTREND", "LONG", 0.001, 100, 100, 1)["status"] == "NO_SETUP"
    assert (
        plan_prices("UPTREND", "LONG", 1, 100, 100.251, 0.01)["reason"] == "ENTRY_DRIFT"
    )
    p = plan_prices("DOWNTREND", "SHORT", 1.01, 100, 100, 0.1)
    assert p["stop"] == "101.6" and p["target"] == "97.0"


def ticker():
    return {
        "success": True,
        "code": 0,
        "data": [
            {
                "symbol": "BTC_USDT",
                "lastPrice": 100,
                "bid1": 99.99,
                "ask1": 100.01,
                "volume24": 10000,
                "amount24": 1000000,
                "timestamp": 1793707200000,
            }
        ],
    }


@pytest.mark.parametrize(
    "key,value",
    [
        ("bid1", 101),
        ("lastPrice", True),
        ("lastPrice", float("inf")),
        ("lastPrice", 0),
        ("amount24", None),
        ("volume24", -1),
        ("symbol", None),
        ("symbol", {}),
        ("timestamp", None),
        ("timestamp", 1793707300000),
        ("timestamp", 1793707100000),
    ],
)
def test_scanner_rejections(key, value):
    payload = ticker()
    payload["data"][0][key] = value
    result = scan(payload, at(1))
    assert result["counts"]["eligible"] == 0


def test_scanner_duplicates_and_envelope():
    payload = ticker()
    payload["data"] *= 2
    result = scan(payload, at(1))
    assert result["counts"] == {"raw": 2, "eligible": 0, "rejected": 2}
    for value in (False, True, None, "0"):
        p = ticker()
        p["code"] = value
        assert scan(p, at(1))["status"] == "ERROR"
    assert scan(ticker(), at(1), http_status=500)["reason"] == "HTTP_ERROR"
    result = scan(ticker(), at(1))
    assert result["counts"]["eligible"] == 1
    assert result["snapshot_id"] != scan(ticker(), at(1))["snapshot_id"]


def test_collector_records_errors(tmp_path):
    c = Collector(tmp_path, transport=lambda url: (503, b"Unavailable"))
    with pytest.raises(DomainError, match="HTTP"):
        c.collect("ticker")
    assert len(list(tmp_path.glob("RAW-*/body.bin"))) == 1
    with pytest.raises(DomainError, match="UNSUPPORTED"):
        c.collect("order")


def test_schema_stamping_and_idempotency(tmp_path):
    s = Store(tmp_path / "s.sqlite")
    c = case()
    s.create_case(c, packet(), at(1))
    r = report(c, "news")
    first = s.import_report(r, "operator", at(1.5))
    assert first["import"]["importer"] == "operator"
    assert s.import_report(r, "other", at(500)) == first
    r["summary"] = "Changed"
    with pytest.raises(DomainError, match="ID_PAYLOAD_CONFLICT"):
        s.import_report(r, "operator", at(1.6))
    r = report(c, "sentiment")
    r["import"] = {"imported_at": at(0)}
    with pytest.raises(DomainError, match="Additional properties"):
        validate_report(r, c, at(1.5))


def test_wait_and_veto(tmp_path):
    s = Store(tmp_path / "s.sqlite")
    assert prepare_decision(s, "WAIT", missing=True)["decision"] == "WAIT"
    d = prepare_decision(s, "VETO", veto=True)
    assert d["decision"] == "SKIP" and d["veto"] and d["dissent"]


def test_single_atomic_slot(system):
    s, e = system
    prepare_decision(s, "CASE-OTHER")

    def attempt(args):
        try:
            return e.admit(args[0], args[1], quote(), NOW)["status"]
        except DomainError as exc:
            return exc.code

    with ThreadPoolExecutor(2) as pool:
        results = list(
            pool.map(attempt, [("CASE-DEMO-001", "one"), ("CASE-OTHER", "two")])
        )
    assert sorted(results) == ["ACCEPTED", "POSITION_SLOT_RESERVED"]
    assert len(s.all("order")) == 1


def test_partial_restart_cancel_and_idempotent_fill(system):
    s, e = system
    o = e.admit("CASE-DEMO-001", "one", quote(), NOW)
    f = e.fill_entry(o["order_id"], "fill1", "1", quote(), NOW)
    assert e.fill_entry(o["order_id"], "fill1", "1", quote(), NOW) == f
    e.cancel(o["order_id"], NOW)
    other = PaperEngine(Store(s.path))
    assert other.reconcile(NOW)["status"] == "OK"
    p = other.summary()["positions"][0]
    assert p["qty"] == "1" and p["protection"] == "ACTIVE"
    assert other.summary()["orders"][0]["status"] == "CANCELLED_REMAINDER"


def test_gap_exit_uses_actual_quote_and_pause_keeps_monitor(system):
    s, e = system
    o = e.admit("CASE-DEMO-001", "one", quote(), NOW)
    e.fill_entry(o["order_id"], "fill1", "1", quote(), NOW)
    e.pause(NOW)
    q = quote("95", at(3))
    result = e.monitor({"DEMO_USDT": q}, at(3))
    assert result["closings"][0][1] == "STOP"
    p = s.all("position")[0]
    assert p["status"] == "CLOSE_PENDING" and p["qty"] == "1"
    fill = e.fill_exit(p["position_id"], "exit1", "0.4", q, at(3))
    assert Decimal(fill["price"]) < 95
    p = s.all("position")[0]
    assert (
        p["qty"] == "0.6"
        and p["status"] == "CLOSE_PENDING"
        and p["protection"] == "ACTIVE"
    )
    e.fill_exit(p["position_id"], "exit2", "0.6", q, at(3))
    assert e.reconcile(at(3))["status"] == "OK"


def test_stale_unpriced_and_persistent_gap_latch(system):
    s, e = system
    o = e.admit("CASE-DEMO-001", "one", quote(), NOW)
    e.fill_entry(o["order_id"], "fill1", "1", quote(), NOW)
    result = e.monitor({"DEMO_USDT": quote()}, at(20))
    assert result["unpriced"] and s.all("position")[0]["qty"] == "1"
    assert e.summary()["equity"] is None
    e.monitor({"DEMO_USDT": quote("100", at(21))}, at(21))
    assert "MONITOR_GAP" in PaperEngine(Store(s.path)).summary()["latched_reasons"]
