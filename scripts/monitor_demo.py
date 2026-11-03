"""Independent DEMO monitor process; no native model calls or order connections."""

import argparse
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from services.coordinator.store import Store
from services.paper.engine import PaperEngine
from services.core import iso, strict_loads, DomainError

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument(
        "--quotes",
        type=Path,
        required=True,
        help="Explicit fictional quote file; actual UTC stamps required",
    )
    p.add_argument("--once", action="store_true")
    args = p.parse_args()
    if os.name == "nt" and not os.environ.get("GTC_VERIFIED_D_VOLUME"):
        raise SystemExit("Verify D: first through launch.ps1")
    engine = PaperEngine(Store(ROOT / "runtime/demo.sqlite"))
    engine.reconcile(iso())
    while True:
        started = time.monotonic()
        try:
            quotes = strict_loads(args.quotes.read_text())
            engine.monitor(quotes, iso())
        except (OSError, DomainError):
            engine.monitor({}, iso())
        if args.once:
            break
        time.sleep(max(0, 1 - (time.monotonic() - started)))
