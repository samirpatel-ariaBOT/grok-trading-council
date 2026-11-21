"""SQLite online backup + integrity check; creates a new file only."""

import sqlite3
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]

if __name__ == "__main__":
    source = ROOT / "runtime/demo.sqlite"
    if not source.exists():
        raise SystemExit("No demo ledger exists.")
    destination = (
        ROOT
        / "runtime/backups"
        / f"demo-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')}.sqlite"
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("xb"):
        pass
    with (
        sqlite3.connect(f"file:{source}?mode=ro", uri=True) as src,
        sqlite3.connect(destination) as dst,
    ):
        src.backup(dst)
        if dst.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise SystemExit("Backup integrity failed.")
    print(destination)
