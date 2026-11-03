"""Print truthful setup status; success never means trading is ready."""
from __future__ import annotations

import argparse
import json
import platform
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from services.configuration.bootstrap import ConfigurationError, load_bootstrap


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=ROOT / "config/bootstrap.json")
    args = parser.parse_args()
    if sys.version_info < (3, 12):
        print(json.dumps({"status": "BLOCKED", "reason": "Python 3.12+ required"}))
        return 2
    try:
        config = load_bootstrap(args.config)
    except ConfigurationError as exc:
        print(json.dumps({"status": "BLOCKED", "reason": str(exc)}))
        return 2
    report = config.report()
    report.update({
        "status": "BOOTSTRAP_VALID_ONLY",
        "python_version": platform.python_version(),
        "platform": platform.system(),
        "project_root": str(ROOT),
        "isolated_environment": sys.prefix != sys.base_prefix,
        "source_document_review": "PENDING_IN_NEW_REPOSITORY",
        "native_bot_profiles": "NOT_CREATED_BY_THIS_PACKAGE",
        "repository_connection": "NOT_CHECKED_BY_THIS_COMMAND",
        "scope": "Configuration diagnostic only; no data collection or trading",
    })
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

