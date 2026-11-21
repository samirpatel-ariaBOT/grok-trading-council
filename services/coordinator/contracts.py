from pathlib import Path
from jsonschema import Draft202012Validator, FormatChecker
from services.core import DomainError, strict_loads, epoch

ROSTER = {
    "chief": "68efd964-33e9-472b-968f-55d5a79281e1",
    "scout": "3e72f86c-abd9-4a79-942c-ebed6b4e1749",
    "news": "fa1e2c0b-fcbb-45f3-92c5-a47b1199c491",
    "sentiment": "dae59091-8eff-41dc-b1f9-2b40ab4d8027",
    "quant": "97ff20ea-ea73-46b0-b44f-2f46bde951dd",
    "guardian": "9b4f77e0-c3c8-4896-9bae-48ba79c78c4b",
    "auditor": "5356768f-5e98-4ff3-9093-449fbf412433",
}
COUNCIL = tuple(role for role in ROSTER if role != "auditor")
ROOT = Path(__file__).resolve().parents[2]
SCHEMA = strict_loads((ROOT / "schemas/report.schema.json").read_text())
Draft202012Validator.check_schema(SCHEMA)
VALIDATOR = Draft202012Validator(SCHEMA, format_checker=FormatChecker())


def validate_report(report, case, now):
    errors = sorted(VALIDATOR.iter_errors(report), key=lambda item: str(item.path))
    if errors:
        raise DomainError(
            "INVALID_REPORT", f"{list(errors[0].path)}: {errors[0].message}"
        )
    if report["bot_id"] != ROSTER[report["role"]]:
        raise DomainError("BOT_ID_MISMATCH")
    for field in ("case_id", "snapshot_id", "strategy_version", "policy_version"):
        if report[field] != case[field]:
            raise DomainError("CONTEXT_MISMATCH", field)
    if (
        not epoch(case["data_cutoff"])
        <= epoch(report["created_at"])
        <= epoch(now)
        < epoch(case["deadline"])
    ):
        raise DomainError("REPORT_EXPIRED_OR_FUTURE")
    if report["role"] == "auditor":
        raise DomainError("AUDITOR_OUTSIDE_COUNCIL")
    if any(
        epoch(ref["available_at"]) > epoch(case["data_cutoff"])
        for ref in report["provenance"]
    ):
        raise DomainError("EVIDENCE_AFTER_CUTOFF")
    return report
