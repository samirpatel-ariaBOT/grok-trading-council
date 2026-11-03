"""One public read-only discovery run; never feeds the DEMO ledger."""

import sys
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from services.data.mexc import Collector
from services.core import DomainError, canonical

if __name__ == "__main__":
    if os.name == "nt" and not os.environ.get("GTC_VERIFIED_D_VOLUME"):
        raise SystemExit("Verify D: through the PowerShell launcher first.")
    try:
        result = Collector(ROOT / "runtime/public_readonly").discover()
        print(
            canonical(
                {
                    k: result[k]
                    for k in ("snapshot_id", "status", "counts", "metadata_status")
                }
            )
        )
    except DomainError as exc:
        print(
            canonical({"status": "BLOCKED", "reason": exc.code, "detail": exc.detail})
        )
        raise SystemExit(2)
