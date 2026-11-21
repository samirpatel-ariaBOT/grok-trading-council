"""Check the SHA-256 inventory of the recorded source snapshot, excluding mutable runtime files."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    manifest = json.loads((ROOT / "BUNDLE_MANIFEST.json").read_text(encoding="utf-8"))
    problems = []
    for relative, expected in manifest["sha256"].items():
        candidate = (ROOT / relative).resolve()
        if not candidate.is_relative_to(ROOT):
            problems.append(f"Invalid path: {relative}")
            continue
        if not candidate.is_file():
            problems.append(f"Missing: {relative}")
        elif hashlib.sha256(candidate.read_bytes()).hexdigest() != expected:
            problems.append(f"Changed: {relative}")
    print(json.dumps({
        "source_snapshot_verified": not problems,
        "files_checked": len(manifest["sha256"]),
        "problems": problems,
        "note": "This checks recorded source bytes, not trading readiness.",
    }, indent=2))
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())

