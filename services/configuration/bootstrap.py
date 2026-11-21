"""Strict setup-only configuration. This is NOT the M01 trading policy engine."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PROJECT_ID = "gtc-fresh-20261102"
FIXED = {
    "schema_version": "bootstrap-0.1",
    "project_id": PROJECT_ID,
    "phase": "SETUP",
    "mode": "PAPER",
    "exchange": "MEXC",
    "market": "CRYPTO_FUTURES",
    "universe": "ALL_ELIGIBLE_CONTRACTS",
    "data_mode": "FIXTURE_ONLY",
    "execution_enabled": False,
    "network_enabled": False,
    "paid_usage_enabled": False,
}
PENDING = (
    "agent_route",
    "contract_family_and_settlement",
    "allowed_directions",
    "timeframes",
    "paper_risk_policy",
    "runtime_host",
    "usage_budget",
)
EXPECTED_KEYS = set(FIXED) | {"pending_choices"}


class ConfigurationError(ValueError):
    """The setup configuration is missing, malformed, or outside its narrow scope."""


@dataclass(frozen=True)
class BootstrapConfig:
    project_id: str
    pending_choices: tuple[str, ...]

    def report(self) -> dict[str, Any]:
        return {
            "schema_version": "bootstrap-report-0.1",
            "project_id": self.project_id,
            "setup_configuration_valid": True,
            "phase": "SETUP",
            "mode": "PAPER",
            "trading_ready": False,
            "paper_engine_implemented": False,
            "live_order_adapter_implemented": False,
            "network_enabled": False,
            "paid_usage_enabled": False,
            "unresolved_choices": list(self.pending_choices),
        }


def _reject_constant(_: str) -> None:
    raise ConfigurationError("Non-finite JSON constants are forbidden.")


def _unique_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ConfigurationError("Duplicate JSON property.")
        result[key] = value
    return result


def parse_bootstrap(text: str) -> BootstrapConfig:
    """Parse a strict JSON document without interpreting environment variables."""
    try:
        value = json.loads(
            text, object_pairs_hook=_unique_pairs, parse_constant=_reject_constant
        )
    except (json.JSONDecodeError, RecursionError) as exc:
        raise ConfigurationError("Malformed JSON configuration.") from exc
    return validate_bootstrap(value)


def validate_bootstrap(value: Any) -> BootstrapConfig:
    """Only the non-executing fresh setup policy is accepted by this release."""
    if not isinstance(value, dict) or set(value) != EXPECTED_KEYS:
        raise ConfigurationError("Unexpected or missing configuration properties.")
    for key, expected in FIXED.items():
        actual = value[key]
        if type(actual) is not type(expected) or actual != expected:
            raise ConfigurationError(f"Invalid setup setting: {key}.")
    pending = value["pending_choices"]
    if not isinstance(pending, dict) or set(pending) != set(PENDING):
        raise ConfigurationError("The unresolved-choice inventory is incomplete.")
    if any(item is not None for item in pending.values()):
        raise ConfigurationError(
            "This bootstrap accepts no active financial or runtime policy. "
            "Approved choices require the later versioned policy implementation."
        )
    return BootstrapConfig(PROJECT_ID, PENDING)


def load_bootstrap(path: Path) -> BootstrapConfig:
    """Read a local UTF-8 file. No HTTP, credentials, exchange calls, or orders."""
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise ConfigurationError("Cannot read the UTF-8 setup configuration.") from exc
    return parse_bootstrap(text)
