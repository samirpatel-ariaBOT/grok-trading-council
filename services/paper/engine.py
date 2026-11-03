"""Atomic deterministic DEMO admission/fills. Never imports an exchange SDK."""

from decimal import Decimal, ROUND_FLOOR
from contextlib import closing
from services.core import (
    DomainError,
    decimal_value as n,
    ds,
    digest,
    epoch,
    fresh_quote,
    tick_round,
)

DEMO_POLICY = {
    "version": "demo-policy-v1",
    "mode": "DEMO",
    "fixture_only": True,
    "initial_equity": "10000",
    "risk_fraction": "0.0025",
    "notional_fraction": "0.15",
    "daily_loss_fraction": "0.01",
    "fee_rate": "0.0006",
    "slippage_bps": "2",
    "max_positions": 1,
    "quote_max_age_seconds": 3,
    "maximum_monitor_gap_seconds": 3,
    "day_timezone": "UTC",
    "funding_model": "ZERO_FICTIONAL_FIXTURE_ONLY",
}


class PaperEngine:
    def __init__(self, store):
        self.store = store

    def initialize_demo(self, now):
        with self.store.transaction() as db:
            if self.store.all("account", db):
                return self.store.get("account", "DEMO", db)
            account = {
                "mode": "DEMO",
                "policy": DEMO_POLICY,
                "cash": DEMO_POLICY["initial_equity"],
                "day": now[:10],
                "day_start_equity": DEMO_POLICY["initial_equity"],
                "paused": False,
                "latched_reasons": [],
                "monitor_at": None,
                "maximum_monitor_gap_seconds": 0,
                "unpriced": False,
            }
            self.store.put(db, "account", "DEMO", account)
            self.store.event(
                db,
                "DEMO_INITIALIZED",
                "DEMO",
                {"fictional": True, "policy": DEMO_POLICY},
                now,
            )
            return account

    def _account(self, db):
        account = self.store.get("account", "DEMO", db)
        if account.get("mode") != "DEMO" or account.get("policy") != DEMO_POLICY:
            raise DomainError("OPERATIONAL_ACTIVATION_DISABLED")
        return account

    def _equity(self, db, account):
        unrealized = Decimal(0)
        for p in self.store.all("position", db):
            if p["status"] == "CLOSED":
                continue
            if p.get("mark") is None:
                raise DomainError("UNPRICED_POSITION")
            sign = 1 if p["side"] == "LONG" else -1
            unrealized += (
                (n(p["mark"]) - n(p["entry"]))
                * sign
                * n(p["qty"])
                * n(p["contract_size"])
            )
        return n(account["cash"]) + unrealized, unrealized

    def _gate(self, db, account, now):
        if account["paused"] or account["latched_reasons"] or account["unpriced"]:
            raise DomainError("ENTRY_PAUSED")
        if (
            not account["monitor_at"]
            or not 0
            <= epoch(now) - epoch(account["monitor_at"])
            <= DEMO_POLICY["maximum_monitor_gap_seconds"]
        ):
            raise DomainError("MONITOR_STALE")
        equity, _ = self._equity(db, account)
        if now[:10] != account["day"]:
            # Rollover only after fresh marking; existing latches are never reset here.
            account.update(day=now[:10], day_start_equity=ds(equity))
        if equity <= n(account["day_start_equity"]) * (
            1 - n(DEMO_POLICY["daily_loss_fraction"])
        ):
            raise DomainError("DAILY_LOSS_LIMIT")
        if equity <= 0:
            raise DomainError("NO_EQUITY")
        return equity

    def admit(self, case_id, request_id, quote, now):
        request = {"case_id": case_id, "quote": quote}
        with self.store.transaction() as db:
            prior = [
                o for o in self.store.all("order", db) if o["request_id"] == request_id
            ]
            if prior:
                if prior[0]["request_hash"] != digest(request):
                    raise DomainError("ID_PAYLOAD_CONFLICT")
                return prior[0]
            account = self._account(db)
            equity = self._gate(db, account, now)
            decision = self.store.get("decision", case_id, db)
            plan = decision.get("plan")
            if (
                decision["decision"] not in ("LONG", "SHORT")
                or decision["veto"]
                or not plan
                or plan["status"] != "PLAN"
                or digest(plan) != decision["plan_hash"]
            ):
                raise DomainError("NO_ADMISSIBLE_DECISION")
            if (
                plan["policy_version"] != DEMO_POLICY["version"]
                or plan["side"] != decision["decision"]
            ):
                raise DomainError("POLICY_OR_DIRECTION_MISMATCH")
            if not epoch(plan["created_at"]) <= epoch(now) < epoch(plan["expires_at"]):
                raise DomainError("PLAN_EXPIRED")
            open_positions = [
                p for p in self.store.all("position", db) if p["status"] != "CLOSED"
            ]
            pending = [
                o
                for o in self.store.all("order", db)
                if o["status"] in ("ACCEPTED", "PARTIAL")
            ]
            if open_positions or pending:
                raise DomainError("POSITION_SLOT_RESERVED")
            if any(o["case_id"] == case_id for o in self.store.all("order", db)):
                raise DomainError("CASE_ALREADY_ADMITTED")
            if any(
                o["plan"]["trigger_key"] == plan["trigger_key"]
                for o in self.store.all("order", db)
            ):
                raise DomainError("TRIGGER_ALREADY_ADMITTED")
            snap = self.store.get("snapshot", plan["snapshot_id"], db)
            if snap.get("fictional") is not True or snap.get("mode") != "DEMO":
                raise DomainError("NON_FIXTURE_EXECUTION_DISABLED")
            metadata = snap["instrument"]
            if (
                metadata["active"] is not True
                or plan["side"] not in metadata["allowed_sides"]
            ):
                raise DomainError("INSTRUMENT_INELIGIBLE")
            if quote.get("symbol") != plan["symbol"]:
                raise DomainError("QUOTE_SYMBOL_MISMATCH")
            bid, ask = fresh_quote(quote, now)
            slip = n(DEMO_POLICY["slippage_bps"]) / 10000
            price = (ask * (1 + slip)) if plan["side"] == "LONG" else (bid * (1 - slip))
            price = tick_round(
                price, n(metadata["tick_size"]), up=plan["side"] == "LONG"
            )
            if not n(plan["entry_min"]) <= price <= n(plan["entry_max"]):
                raise DomainError("ENTRY_DRIFT")
            stop, target = (
                n(plan["stop"], positive=True),
                n(plan["target"], positive=True),
            )
            if not (
                stop < price < target
                if plan["side"] == "LONG"
                else target < price < stop
            ):
                raise DomainError("INVALID_ROUNDED_PRICES")
            multiplier = n(metadata["contract_size"], positive=True)
            step = n(metadata["qty_step"], positive=True)
            # Worst permitted entry, stop slippage and both fees, per contract.
            worst = n(
                plan["entry_max"] if plan["side"] == "LONG" else plan["entry_min"],
                positive=True,
            )
            worst_exit = tick_round(
                stop * (1 - slip if plan["side"] == "LONG" else 1 + slip),
                n(metadata["tick_size"]),
                up=plan["side"] == "SHORT",
            )
            if worst_exit <= 0:
                raise DomainError("INVALID_COST_ADJUSTED_STOP")
            unit_risk = (
                abs(worst - worst_exit)
                + (worst + worst_exit) * n(DEMO_POLICY["fee_rate"])
            ) * multiplier
            cap = equity * n(DEMO_POLICY["notional_fraction"])
            notional_price = n(plan["entry_max"], positive=True)
            qty = min(
                equity * n(DEMO_POLICY["risk_fraction"]) / unit_risk,
                cap / (notional_price * multiplier),
                n(metadata["max_qty"], positive=True),
            )
            qty = (qty / step).to_integral_value(rounding=ROUND_FLOOR) * step
            if qty < n(metadata["min_qty"], positive=True) or qty <= 0:
                raise DomainError("BELOW_MINIMUM_QUANTITY")
            risk, notional = qty * unit_risk, qty * notional_price * multiplier
            if risk > equity * n(DEMO_POLICY["risk_fraction"]) or notional > cap:
                raise DomainError("ROUNDED_RISK_EXCEEDED")
            order = {
                "order_id": f"ORD-{request_id}",
                "request_id": request_id,
                "request_hash": digest(request),
                "case_id": case_id,
                "plan": plan,
                "qty": ds(qty),
                "filled_qty": "0",
                "status": "ACCEPTED",
                "reserved_risk": ds(risk),
                "reserved_notional": ds(notional),
                "admitted_at": now,
                "mode": "DEMO",
            }
            self.store.put(db, "order", order["order_id"], order)
            self.store.put(db, "account", "DEMO", account, replace=True)
            self.store.event(
                db,
                "ORDER_ADMITTED",
                case_id,
                {
                    "order_id": order["order_id"],
                    "qty": order["qty"],
                    "reserved_risk": order["reserved_risk"],
                },
                now,
            )
            return order

    def fill_entry(self, order_id, fill_id, quantity, quote, now):
        request = {"order_id": order_id, "quantity": quantity, "quote": quote}
        with self.store.transaction() as db:
            existing = [
                f for f in self.store.all("fill", db) if f["fill_id"] == fill_id
            ]
            if existing:
                if existing[0]["request_hash"] != digest(request):
                    raise DomainError("ID_PAYLOAD_CONFLICT")
                return existing[0]
            account = self._account(db)
            self._gate(db, account, now)
            order = self.store.get("order", order_id, db)
            plan = order["plan"]
            if order["status"] not in ("ACCEPTED", "PARTIAL") or epoch(now) >= epoch(
                plan["expires_at"]
            ):
                raise DomainError("ORDER_NOT_FILLABLE")
            q = n(quantity, positive=True)
            remaining = n(order["qty"]) - n(order["filled_qty"])
            metadata = self.store.get("snapshot", plan["snapshot_id"], db)["instrument"]
            if q > remaining or q % n(metadata["qty_step"]):
                raise DomainError("INVALID_FILL_QUANTITY")
            if quote.get("symbol") != plan["symbol"]:
                raise DomainError("QUOTE_SYMBOL_MISMATCH")
            bid, ask = fresh_quote(quote, now)
            slip = n(DEMO_POLICY["slippage_bps"]) / 10000
            price = ask * (1 + slip) if plan["side"] == "LONG" else bid * (1 - slip)
            price = tick_round(
                price, n(metadata["tick_size"]), up=plan["side"] == "LONG"
            )
            if not n(plan["entry_min"]) <= price <= n(plan["entry_max"]):
                raise DomainError("ENTRY_DRIFT")
            multiplier = n(plan["contract_size"])
            fee = price * q * multiplier * n(DEMO_POLICY["fee_rate"])
            pos_id = f"POS-{order_id}"
            old = [
                p for p in self.store.all("position", db) if p["position_id"] == pos_id
            ]
            if old and old[0]["status"] != "OPEN":
                raise DomainError("POSITION_NOT_OPEN")
            p = (
                old[0]
                if old
                else {
                    "position_id": pos_id,
                    "order_id": order_id,
                    "case_id": order["case_id"],
                    "symbol": plan["symbol"],
                    "side": plan["side"],
                    "qty": "0",
                    "entry": ds(price),
                    "contract_size": plan["contract_size"],
                    "stop": plan["stop"],
                    "target": plan["target"],
                    "opened_at": now,
                    "max_hold_seconds": plan["max_hold_seconds"],
                    "status": "OPEN",
                    "protection": "ACTIVE",
                    "fees": "0",
                    "realized_pnl": "0",
                }
            )
            total = n(p["qty"]) + q
            p.update(
                entry=ds((n(p["entry"]) * n(p["qty"]) + price * q) / total),
                qty=ds(total),
                mark=ds(bid if p["side"] == "LONG" else ask),
                mark_at=now,
                fees=ds(n(p["fees"]) + fee),
            )
            order["filled_qty"] = ds(n(order["filled_qty"]) + q)
            order["status"] = (
                "FILLED" if n(order["filled_qty"]) == n(order["qty"]) else "PARTIAL"
            )
            account["cash"] = ds(n(account["cash"]) - fee)
            fill = {
                "fill_id": fill_id,
                "request_hash": digest(request),
                "order_id": order_id,
                "position_id": pos_id,
                "kind": "ENTRY",
                "quantity": ds(q),
                "price": ds(price),
                "fee": ds(fee),
                "cash_delta": ds(-fee),
                "at": now,
                "liquidity_model": "EXPLICIT_FIXTURE_QUANTITY; no real order book simulation",
            }
            for kind, identity, obj in (
                ("position", pos_id, p),
                ("order", order_id, order),
                ("account", "DEMO", account),
            ):
                self.store.put(db, kind, identity, obj, replace=True)
            self.store.put(db, "fill", fill_id, fill)
            self.store.event(db, "ENTRY_FILLED", p["case_id"], fill, now)
            return fill

    def cancel(self, order_id, now):
        with self.store.transaction() as db:
            o = self.store.get("order", order_id, db)
            if o["status"] in ("ACCEPTED", "PARTIAL"):
                o.update(
                    status="CANCELLED_REMAINDER",
                    reserved_notional="0",
                    reserved_risk="0",
                )
                self.store.put(db, "order", order_id, o, replace=True)
                self.store.event(
                    db,
                    "ORDER_CANCELLED",
                    o["case_id"],
                    {"order_id": order_id, "filled_qty": o["filled_qty"]},
                    now,
                )
            return o

    def request_close(self, position_id, now, reason="OPERATOR_CLOSE"):
        with self.store.transaction() as db:
            p = self.store.get("position", position_id, db)
            if p["status"] == "CLOSED":
                return p
            o = self.store.get("order", p["order_id"], db)
            if o["status"] in ("ACCEPTED", "PARTIAL"):
                o["status"] = "CANCELLED_REMAINDER"
                self.store.put(db, "order", o["order_id"], o, replace=True)
            if p["status"] != "CLOSE_PENDING":
                p.update(
                    status="CLOSE_PENDING", close_reason=reason, close_requested_at=now
                )
                self.store.put(db, "position", position_id, p, replace=True)
                self.store.event(
                    db,
                    "CLOSE_REQUESTED",
                    p["case_id"],
                    {"position_id": position_id, "reason": reason},
                    now,
                )
            return p

    def fill_exit(self, position_id, fill_id, quantity, quote, now):
        request = {"position_id": position_id, "quantity": quantity, "quote": quote}
        with self.store.transaction() as db:
            old = [f for f in self.store.all("fill", db) if f["fill_id"] == fill_id]
            if old:
                if old[0]["request_hash"] != digest(request):
                    raise DomainError("ID_PAYLOAD_CONFLICT")
                return old[0]
            account = self._account(db)
            p = self.store.get("position", position_id, db)
            if p["status"] != "CLOSE_PENDING":
                raise DomainError("NO_EXIT_REQUEST")
            q = n(quantity, positive=True)
            plan = self.store.get("order", p["order_id"], db)["plan"]
            step = n(
                self.store.get("snapshot", plan["snapshot_id"], db)["instrument"][
                    "qty_step"
                ],
                positive=True,
            )
            if q > n(p["qty"]) or q % step:
                raise DomainError("REDUCE_ONLY")
            if quote.get("symbol") != p["symbol"]:
                raise DomainError("QUOTE_SYMBOL_MISMATCH")
            bid, ask = fresh_quote(quote, now)
            slip = n(DEMO_POLICY["slippage_bps"]) / 10000
            price = bid * (1 - slip) if p["side"] == "LONG" else ask * (1 + slip)
            price = tick_round(price, n(plan["tick_size"]), up=p["side"] == "SHORT")
            if price <= 0:
                raise DomainError("INVALID_FILL_PRICE")
            sign = 1 if p["side"] == "LONG" else -1
            gross = (price - n(p["entry"])) * sign * q * n(p["contract_size"])
            fee = price * q * n(p["contract_size"]) * n(DEMO_POLICY["fee_rate"])
            p.update(
                qty=ds(n(p["qty"]) - q),
                fees=ds(n(p["fees"]) + fee),
                realized_pnl=ds(n(p["realized_pnl"]) + gross),
                mark=ds(bid if p["side"] == "LONG" else ask),
                mark_at=now,
            )
            if n(p["qty"]) == 0:
                p.update(status="CLOSED", protection="CLOSED", closed_at=now)
            account["cash"] = ds(n(account["cash"]) + gross - fee)
            fill = {
                "fill_id": fill_id,
                "request_hash": digest(request),
                "position_id": position_id,
                "kind": "EXIT",
                "quantity": ds(q),
                "price": ds(price),
                "fee": ds(fee),
                "realized_pnl": ds(gross),
                "cash_delta": ds(gross - fee),
                "at": now,
                "reduce_only": True,
            }
            self.store.put(db, "fill", fill_id, fill)
            self.store.put(db, "position", position_id, p, replace=True)
            self.store.put(db, "account", "DEMO", account, replace=True)
            self.store.event(db, "EXIT_FILLED", p["case_id"], fill, now)
            return fill

    def monitor(self, quotes, now):
        """Mark/latch/trigger only; stale quotes never manufacture exit fills."""
        closings = []
        with self.store.transaction() as db:
            a = self._account(db)
            gap = epoch(now) - epoch(a["monitor_at"]) if a["monitor_at"] else 0
            if gap < 0:
                raise DomainError("CLOCK_REVERSED")
            if gap > DEMO_POLICY["maximum_monitor_gap_seconds"]:
                a["latched_reasons"] = sorted(
                    set(a["latched_reasons"] + ["MONITOR_GAP"])
                )
            a.update(
                monitor_at=now,
                maximum_monitor_gap_seconds=max(a["maximum_monitor_gap_seconds"], gap),
                unpriced=False,
            )
            for p in self.store.all("position", db):
                if p["status"] == "CLOSED":
                    continue
                try:
                    quote = quotes[p["symbol"]]
                    if quote.get("symbol") != p["symbol"]:
                        raise DomainError("QUOTE_SYMBOL_MISMATCH")
                    bid, ask = fresh_quote(quote, now)
                    mark = bid if p["side"] == "LONG" else ask
                    p.update(mark=ds(mark), mark_at=now, protection="ACTIVE")
                    stop = (
                        mark <= n(p["stop"])
                        if p["side"] == "LONG"
                        else mark >= n(p["stop"])
                    )
                    target = (
                        mark >= n(p["target"])
                        if p["side"] == "LONG"
                        else mark <= n(p["target"])
                    )
                    hold = epoch(now) - epoch(p["opened_at"]) >= p["max_hold_seconds"]
                    if stop or target or hold or p["status"] == "CLOSE_PENDING":
                        closings.append(
                            (
                                p["position_id"],
                                "STOP"
                                if stop
                                else "TARGET"
                                if target
                                else "MAX_HOLD"
                                if hold
                                else p.get("close_reason", "OPERATOR_CLOSE"),
                            )
                        )
                except (DomainError, KeyError):
                    p.update(mark=None, protection="UNPRICED")
                    a["unpriced"] = True
                self.store.put(db, "position", p["position_id"], p, replace=True)
            if not a["unpriced"]:
                equity, _ = self._equity(db, a)
                if equity <= n(a["day_start_equity"]) * (
                    1 - n(DEMO_POLICY["daily_loss_fraction"])
                ):
                    a["latched_reasons"] = sorted(
                        set(a["latched_reasons"] + ["DAILY_LOSS_LIMIT"])
                    )
            self.store.put(db, "account", "DEMO", a, replace=True)
            self.store.event(
                db,
                "MONITOR_TICK",
                "DEMO",
                {"gap_seconds": gap, "unpriced": a["unpriced"]},
                now,
            )
        for position_id, reason in closings:
            self.request_close(position_id, now, reason)
        return {"closings": closings, "gap_seconds": gap, "unpriced": a["unpriced"]}

    def pause(self, now):
        with self.store.transaction() as db:
            a = self._account(db)
            a["paused"] = True
            self.store.put(db, "account", "DEMO", a, replace=True)
            self.store.event(db, "ENTRIES_PAUSED", "DEMO", {}, now)
        for o in self.store.all("order"):
            self.cancel(o["order_id"], now)
        return a

    def reconcile(self, now):
        with self.store.transaction() as db:
            a = self._account(db)
            expected = n(DEMO_POLICY["initial_equity"]) + sum(
                (n(f["cash_delta"]) for f in self.store.all("fill", db)), Decimal(0)
            )
            problems = []
            if expected != n(a["cash"]):
                problems.append("CASH_MISMATCH")
            fills = self.store.all("fill", db)
            for p in self.store.all("position", db):
                quantity = sum(
                    (
                        n(f["quantity"]) * (1 if f["kind"] == "ENTRY" else -1)
                        for f in fills
                        if f["position_id"] == p["position_id"]
                    ),
                    Decimal(0),
                )
                if quantity != n(p["qty"]) or quantity < 0:
                    problems.append("POSITION_MISMATCH")
            if problems:
                a["latched_reasons"] = sorted(set(a["latched_reasons"] + problems))
                self.store.put(db, "account", "DEMO", a, replace=True)
            self.store.event(db, "RECONCILED", "DEMO", {"problems": problems}, now)
            return {"status": "OK" if not problems else "BLOCKED", "problems": problems}

    def summary(self):
        with closing(self.store.connect()) as db:
            a = self._account(db)
            try:
                equity, unrealized = self._equity(db, a)
                values = {"equity": ds(equity), "unrealized_pnl": ds(unrealized)}
            except DomainError:
                values = {"equity": None, "unrealized_pnl": None}
            return {
                **a,
                **values,
                "positions": self.store.all("position", db),
                "orders": self.store.all("order", db),
                "fills": self.store.all("fill", db),
            }
