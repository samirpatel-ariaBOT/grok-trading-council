"""Explicit fictional fixtures. These are not outputs from native Grok bots."""

from datetime import timedelta
from decimal import Decimal
from services.core import iso, utc, ds
from services.coordinator.contracts import ROSTER, COUNCIL
from services.coordinator.store import Store
from services.paper.engine import PaperEngine, DEMO_POLICY

T0 = "2026-11-03T12:00:00.000000Z"
NOW = "2026-11-03T12:00:02.400000Z"


def at(seconds):
    return iso(utc(T0) + timedelta(seconds=seconds))


def quote(price="100", when=None):
    price = Decimal(price)
    return {
        "symbol": "DEMO_USDT",
        "bid": ds(price),
        "ask": ds(price + Decimal(".01")),
        "source_at": when or at(0.8),
        "received_at": when or at(0.9),
        "clock_uncertainty_seconds": "0.05",
    }


def packet(identity="SNAP-DEMO-001"):
    hourly = []
    candles = []
    for i in range(600):
        value = Decimal(90) + Decimal(i) / 100
        start = utc(T0) - timedelta(hours=600 - i)
        hourly.append(
            {
                "open_at": iso(start),
                "close_at": iso(start + timedelta(hours=1)),
                "available_at": iso(start + timedelta(hours=1, milliseconds=100)),
                "open": ds(value),
                "high": ds(value + 1),
                "low": ds(value - 1),
                "close": ds(value),
                "volume": "100",
            }
        )
    for i in range(40):
        start = utc(T0) - timedelta(minutes=15 * (40 - i))
        candles.append(
            {
                "open_at": iso(start),
                "close_at": iso(start + timedelta(minutes=15)),
                "available_at": iso(start + timedelta(minutes=15, milliseconds=100)),
                "open": "99.5",
                "high": "99.8" if i < 39 else "100.1",
                "low": "99",
                "close": "99.5" if i < 39 else "100",
                "volume": "100" if i < 39 else "200",
            }
        )
    return {
        "snapshot_id": identity,
        "fictional": True,
        "mode": "DEMO",
        "hourly": hourly,
        "candles": candles,
        "quote": quote(),
        "instrument": {
            "symbol": "DEMO_USDT",
            "family": "LINEAR_PERPETUAL",
            "active": True,
            "allowed_sides": ["LONG", "SHORT"],
            "contract_size": "1",
            "tick_size": "0.01",
            "qty_step": "0.01",
            "min_qty": "0.01",
            "max_qty": "10000",
            "base": "DEMO",
            "settlement": "USDT",
            "source": "Fictional test metadata",
        },
        "costs": {
            "fee_rate": "0.0006",
            "slippage_bps": "2",
            "funding": "ZERO_FICTIONAL_FIXTURE_ONLY",
        },
    }


def case(identity="CASE-DEMO-001", snapshot_id="SNAP-DEMO-001"):
    return {
        "case_id": identity,
        "snapshot_id": snapshot_id,
        "strategy_version": "baseline-v1",
        "policy_version": "demo-policy-v1",
        "data_cutoff": at(1),
        "deadline": at(120),
        "symbol": "DEMO_USDT",
        "fixture": True,
    }


def report(c, role, *, phase="INITIAL", plan_hash=None, veto=False, missing=False):
    payloads = {
        "chief": {
            "decision": "LONG",
            "plan_hash": plan_hash,
            "rationale": "Fictional fixture; preserve all blockers.",
        },
        "scout": {
            "result": "SHORTLIST",
            "symbols": ["DEMO_USDT"],
            "filter_version": "fixture-v1",
        },
        "news": {
            "assessment": "NO_VERIFIED_EVENT",
            "claims": [],
            "coverage": "Fixture only; no live news research.",
        },
        "sentiment": {
            "assessment": "UNKNOWN",
            "coverage": "Fixture: unavailable optional sentiment feed explicitly declared.",
            "collection_start": at(-3600),
            "collection_end": at(0),
        },
        "quant": {
            "result": "PLAN",
            "plan_hash": plan_hash,
            "rationale": "Numbers must be recomputed by conventional baseline.",
        },
        "guardian": {
            "verdict": "VETO" if veto else "PASS",
            "plan_hash": plan_hash,
            "rationale": "Fixture veto must survive favourable reports."
            if veto
            else "Fixture: review exact proposal hash.",
        },
        "auditor": {
            "proposal": "Fixture experiment proposal only.",
            "activation": False,
            "evidence_ids": [],
        },
    }
    return {
        "schema_version": "3.0",
        "report_id": f"R-{c['case_id']}-{role}-{phase}",
        "case_id": c["case_id"],
        "snapshot_id": c["snapshot_id"],
        "bot_id": ROSTER[role],
        "role": role,
        "instruction_version": "fixture-brief-v1",
        "strategy_version": "baseline-v1",
        "policy_version": "demo-policy-v1",
        "created_at": at(1.1 if phase == "INITIAL" else 2.1),
        "phase": phase,
        "non_executable": True,
        "summary": f"SOFTWARE FIXTURE — {role}; not a native bot acknowledgement.",
        "missing_evidence": ["Required evidence omitted by fixture"] if missing else [],
        "dissent": ["Fixture objection retained"] if veto else [],
        "provenance": [
            {
                "evidence_id": "FIXTURE-001",
                "source_url": "urn:gtc:fictional-fixture:001",
                "available_at": at(0.1),
                "claim": "Synthetic demonstration values only",
            }
        ],
        "payload": payloads[role],
    }


def prepare_decision(store, identity="CASE-DEMO-001", *, veto=False, missing=False):
    c = case(identity, "SNAP-" + identity)
    store.create_case(c, packet(c["snapshot_id"]), at(1))
    for role in COUNCIL:
        store.import_report(
            report(
                c,
                role,
                veto=veto and role == "guardian",
                missing=missing and role == "news",
            ),
            "fixture-generator",
            at(1.5),
        )
    released = store.release(c["case_id"], at(2))
    for role in ("chief", "guardian"):
        store.import_report(
            report(
                c,
                role,
                phase="FINAL",
                plan_hash=released["proposal_hash"],
                veto=veto and role == "guardian",
            ),
            "fixture-generator",
            at(2.2),
        )
    return store.decide(c["case_id"], at(2.3))


def seed(path):
    store = Store(path)
    engine = PaperEngine(store)
    if store.all("account"):
        return store, engine
    engine.initialize_demo(at(0))
    prepare_decision(store, "CASE-DEMO-WAIT", missing=True)
    prepare_decision(store, "CASE-DEMO-VETO", veto=True)
    prepare_decision(store)
    engine.monitor({}, NOW)
    order = engine.admit("CASE-DEMO-001", "DEMO-ENTRY-001", quote(), NOW)
    # Deliberate partial fill: remaining quantity stays visible and reserved.
    q = (Decimal(order["qty"]) / 2).quantize(Decimal(".01"))
    engine.fill_entry(order["order_id"], "DEMO-FILL-001", ds(q), quote(), NOW)
    engine.reconcile(NOW)
    with store.transaction() as db:
        store.put(db, "clock", "DEMO", {"at": NOW, "kind": "FROZEN_FICTIONAL_CLOCK"})
        store.put(
            db,
            "draft",
            "policy",
            {
                "status": "UNAPPROVED",
                "native_route": "NATIVE_GROK_BOTS",
                "local_root": "D:\\GrokTradingCouncil",
                "proposal": DEMO_POLICY,
                "note": "DEMO values only; no operational policy accepted.",
            },
        )
    return store, engine
