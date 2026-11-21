"""Adversarial inputs for the setup boundary; these are not trading-system tests."""
from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from services.configuration.bootstrap import ConfigurationError, parse_bootstrap

BASE = json.loads((ROOT / "config/bootstrap.json").read_text(encoding="utf-8"))


class SetupBoundaryTests(unittest.TestCase):
    def reject_change(self, name, value):
        changed = copy.deepcopy(BASE)
        changed[name] = value
        with self.assertRaises(ConfigurationError):
            parse_bootstrap(json.dumps(changed))

    def test_valid_draft_remains_unready(self):
        report = parse_bootstrap(json.dumps(BASE)).report()
        self.assertFalse(report["trading_ready"])
        self.assertFalse(report["paper_engine_implemented"])
        self.assertFalse(report["live_order_adapter_implemented"])

    def test_live_mode_cannot_be_enabled(self):
        self.reject_change("mode", "LIVE")

    def test_execution_cannot_be_enabled(self):
        self.reject_change("execution_enabled", True)

    def test_network_cannot_be_enabled(self):
        self.reject_change("network_enabled", True)

    def test_paid_usage_cannot_be_enabled(self):
        self.reject_change("paid_usage_enabled", True)

    def test_numeric_zero_is_not_false(self):
        self.reject_change("execution_enabled", 0)

    def test_string_false_is_not_false(self):
        self.reject_change("execution_enabled", "false")

    def test_duplicate_mode_is_rejected(self):
        text = json.dumps(BASE).replace('"mode": "PAPER"', '"mode": "LIVE", "mode": "PAPER"')
        with self.assertRaises(ConfigurationError):
            parse_bootstrap(text)

    def test_unknown_fields_are_rejected(self):
        self.reject_change("inherited_policy", {"capital": 10000})

    def test_missing_field_is_rejected(self):
        changed = copy.deepcopy(BASE)
        del changed["execution_enabled"]
        with self.assertRaises(ConfigurationError):
            parse_bootstrap(json.dumps(changed))

    def test_foreign_project_identity_is_rejected(self):
        self.reject_change("project_id", "another-project")

    def test_different_exchange_is_rejected(self):
        self.reject_change("exchange", "OTHER")

    def test_financial_defaults_cannot_be_silently_activated(self):
        changed = copy.deepcopy(BASE)
        changed["pending_choices"]["paper_risk_policy"] = {"risk_per_trade": 0.0025}
        with self.assertRaises(ConfigurationError):
            parse_bootstrap(json.dumps(changed))

    def test_pending_choices_cannot_be_omitted(self):
        changed = copy.deepcopy(BASE)
        del changed["pending_choices"]["runtime_host"]
        with self.assertRaises(ConfigurationError):
            parse_bootstrap(json.dumps(changed))

    def test_non_finite_json_is_rejected(self):
        text = json.dumps(BASE).replace('"paper_risk_policy": null', '"paper_risk_policy": NaN')
        with self.assertRaises(ConfigurationError):
            parse_bootstrap(text)

    def test_array_is_not_a_configuration(self):
        with self.assertRaises(ConfigurationError):
            parse_bootstrap("[]")

    def test_malformed_json_is_rejected(self):
        with self.assertRaises(ConfigurationError):
            parse_bootstrap("{")

    def test_cli_invalid_configuration_returns_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.json"
            path.write_text("{}", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, "-I", str(ROOT / "scripts/check_setup.py"), "--config", str(path)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 2)
            self.assertEqual(json.loads(result.stdout)["status"], "BLOCKED")

    def test_setup_refuses_an_existing_environment(self):
        spec = importlib.util.spec_from_file_location(
            "create_environment", ROOT / "scripts/create_environment.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".project-id").write_text("gtc-fresh-20261102\n", encoding="utf-8")
            (root / ".venv").mkdir()
            sentinel = root / ".venv" / "keep.txt"
            sentinel.write_text("keep", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                module.check_destination(root)
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "keep")


if __name__ == "__main__":
    unittest.main()

