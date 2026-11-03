"""Small transactional store; all mutations append an audit event."""

from contextlib import contextmanager, closing
from pathlib import Path
import sqlite3
import uuid
from services.core import DomainError, canonical, strict_loads, digest, epoch
from services.features.baseline import propose
from services.coordinator.contracts import validate_report, COUNCIL


class Store:
    def __init__(self, path):
        self.path = str(path)
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with closing(self.connect()) as db:
            db.executescript("""PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS objects(kind TEXT NOT NULL,id TEXT NOT NULL,payload TEXT NOT NULL,hash TEXT NOT NULL,PRIMARY KEY(kind,id));
            CREATE TABLE IF NOT EXISTS events(seq INTEGER PRIMARY KEY AUTOINCREMENT,id TEXT UNIQUE NOT NULL,at TEXT NOT NULL,kind TEXT NOT NULL,entity TEXT NOT NULL,payload TEXT NOT NULL);
            """)

    def connect(self):
        db = sqlite3.connect(self.path, timeout=5, isolation_level=None)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("PRAGMA busy_timeout=5000")
        return db

    @contextmanager
    def transaction(self):
        db = self.connect()
        try:
            db.execute("BEGIN IMMEDIATE")
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def get(self, kind, identity, db=None):
        if db is None:
            with closing(self.connect()) as conn:
                return self.get(kind, identity, conn)
        row = db.execute(
            "SELECT payload FROM objects WHERE kind=? AND id=?", (kind, identity)
        ).fetchone()
        if row is None:
            raise DomainError("NOT_FOUND", f"{kind}:{identity}")
        return strict_loads(row[0])

    def all(self, kind, db=None):
        if db is None:
            with closing(self.connect()) as conn:
                return self.all(kind, conn)
        return [
            strict_loads(row[0])
            for row in db.execute(
                "SELECT payload FROM objects WHERE kind=? ORDER BY id", (kind,)
            )
        ]

    def put(self, db, kind, identity, value, *, replace=False):
        existing = db.execute(
            "SELECT hash FROM objects WHERE kind=? AND id=?", (kind, identity)
        ).fetchone()
        h = digest(value)
        if existing and not replace:
            if existing[0] != h:
                raise DomainError("ID_PAYLOAD_CONFLICT")
            return False
        db.execute(
            "INSERT INTO objects VALUES(?,?,?,?) ON CONFLICT(kind,id) DO UPDATE SET payload=excluded.payload,hash=excluded.hash",
            (kind, identity, canonical(value), h),
        )
        return True

    def event(self, db, kind, entity, payload, now):
        epoch(now)
        db.execute(
            "INSERT INTO events(id,at,kind,entity,payload) VALUES(?,?,?,?,?)",
            (str(uuid.uuid4()), now, kind, entity, canonical(payload)),
        )

    def events(self):
        with closing(self.connect()) as db:
            return [
                {**dict(row), "payload": strict_loads(row["payload"])}
                for row in db.execute("SELECT * FROM events ORDER BY seq")
            ]

    def create_case(self, case, snapshot, now):
        if (
            case["strategy_version"] != "baseline-v1"
            or case["snapshot_id"] != snapshot["snapshot_id"]
            or not epoch(case["data_cutoff"]) <= epoch(now) < epoch(case["deadline"])
        ):
            raise DomainError("INVALID_CASE")
        with self.transaction() as db:
            self.put(db, "snapshot", snapshot["snapshot_id"], snapshot)
            if self.put(
                db,
                "case",
                case["case_id"],
                {**case, "status": "COLLECTING", "isolation": "INSTRUCTION_ONLY"},
            ):
                self.event(
                    db,
                    "CASE_CREATED",
                    case["case_id"],
                    {"snapshot_id": snapshot["snapshot_id"]},
                    now,
                )

    def import_report(self, report, operator, now):
        if not isinstance(operator, str) or not operator.strip() or len(operator) > 100:
            raise DomainError("OPERATOR_REQUIRED")
        with self.transaction() as db:
            # Replay is checked before freshness: exact duplicate imports are idempotent.
            existing = db.execute(
                "SELECT payload FROM objects WHERE kind='report' AND id=?",
                (report.get("report_id"),),
            ).fetchone()
            if existing:
                old = strict_loads(existing[0])
                if digest(old["report"]) != digest(report):
                    raise DomainError("ID_PAYLOAD_CONFLICT")
                return old
            case = self.get("case", report.get("case_id"), db)
            if case["status"] == "DECIDED":
                raise DomainError("CASE_CLOSED")
            validate_report(report, case, now)
            if report["phase"] == "INITIAL" and case["status"] != "COLLECTING":
                raise DomainError("FIRST_ROUND_CLOSED")
            if report["phase"] == "FINAL" and case["status"] != "CHALLENGE":
                raise DomainError("CHALLENGE_NOT_OPEN")
            prior = [
                item["report"]
                for item in self.all("report", db)
                if item["report"]["case_id"] == case["case_id"]
                and item["report"]["role"] == report["role"]
                and item["report"]["phase"] == report["phase"]
            ]
            if prior:
                raise DomainError("ROUND_REPORT_ALREADY_EXISTS")
            wrapped = {
                "report": report,
                "import": {
                    "importer": operator,
                    "imported_at": now,
                    "content_sha256": digest(report),
                    "origin": "MANUAL_JSON",
                    "identity_verification": "OPERATOR_ATTESTED; not native API authenticated",
                },
            }
            self.put(db, "report", report["report_id"], wrapped)
            self.event(
                db,
                "REPORT_IMPORTED",
                case["case_id"],
                {
                    "report_id": report["report_id"],
                    "role": report["role"],
                    "phase": report["phase"],
                    "non_executable": True,
                },
                now,
            )
            return wrapped

    def release(self, case_id, now):
        with self.transaction() as db:
            case = self.get("case", case_id, db)
            if case["status"] != "COLLECTING" or epoch(now) >= epoch(case["deadline"]):
                raise DomainError("CASE_NOT_COLLECTING")
            reports = [
                r["report"]
                for r in self.all("report", db)
                if r["report"]["case_id"] == case_id
            ]
            if set(r["role"] for r in reports) != set(COUNCIL):
                raise DomainError("MISSING_FIRST_ROUND")
            snapshot = self.get("snapshot", case["snapshot_id"], db)
            plan = propose(case, snapshot, now)
            case.update(status="CHALLENGE", proposal=plan, proposal_hash=digest(plan))
            self.put(db, "case", case_id, case, replace=True)
            self.event(
                db,
                "FIRST_ROUND_RELEASED",
                case_id,
                {
                    "reports": [r["report_id"] for r in reports],
                    "proposal_hash": case["proposal_hash"],
                },
                now,
            )
            return case

    def decide(self, case_id, now):
        with self.transaction() as db:
            case = self.get("case", case_id, db)
            if case["status"] == "DECIDED":
                return self.get("decision", case_id, db)
            reports = [
                r["report"]
                for r in self.all("report", db)
                if r["report"]["case_id"] == case_id
            ]
            reasons = []
            final = {r["role"]: r for r in reports if r["phase"] == "FINAL"}
            initial = {r["role"]: r for r in reports if r["phase"] == "INITIAL"}
            verdict = "WAIT"
            veto = any(
                r["role"] == "guardian" and r["payload"]["verdict"] == "VETO"
                for r in reports
            )
            if veto:
                verdict = "SKIP"
                reasons.append("GUARDIAN_VETO")
            elif epoch(now) >= epoch(case["deadline"]):
                reasons.append("CASE_EXPIRED")
            elif (
                set(initial) != set(COUNCIL)
                or "chief" not in final
                or "guardian" not in final
            ):
                reasons.append("MISSING_REQUIRED_REPORT")
            elif any(r["missing_evidence"] for r in reports):
                reasons.append("MISSING_EVIDENCE")
            elif final["guardian"]["payload"]["verdict"] != "PASS":
                reasons.append("GUARDIAN_NOT_PASS")
            elif case.get("proposal", {}).get("status") != "PLAN":
                verdict = "SKIP"
                reasons.append(case.get("proposal", {}).get("reason", "NO_SETUP"))
            elif any(
                final[role]["payload"]["plan_hash"] != case["proposal_hash"]
                for role in ("chief", "guardian")
            ):
                reasons.append("PLAN_HASH_MISMATCH")
            elif epoch(now) >= epoch(case["proposal"]["expires_at"]):
                reasons.append("PLAN_EXPIRED")
            else:
                verdict = final["chief"]["payload"]["decision"]
                if verdict in ("LONG", "SHORT") and verdict != case["proposal"]["side"]:
                    verdict = "WAIT"
                    reasons.append("DIRECTION_MISMATCH")
            decision = {
                "decision_id": f"DEC-{case_id}",
                "case_id": case_id,
                "snapshot_id": case["snapshot_id"],
                "decision": verdict,
                "veto": veto,
                "reasons": reasons,
                "dissent": [d for r in reports for d in r["dissent"]],
                "report_ids": [r["report_id"] for r in reports],
                "created_at": now,
                "non_executable": True,
                "plan": case.get("proposal"),
                "plan_hash": case.get("proposal_hash"),
            }
            self.put(db, "decision", case_id, decision)
            case["status"] = "DECIDED"
            self.put(db, "case", case_id, case, replace=True)
            self.event(
                db,
                "DECISION_RECORDED",
                case_id,
                {"decision": verdict, "veto": veto, "reasons": reasons},
                now,
            )
            return decision
