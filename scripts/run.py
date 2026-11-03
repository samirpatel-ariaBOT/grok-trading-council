"""Launch only the isolated fixture demo; no operational activation switch."""

import argparse
from pathlib import Path
import os
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from services.api import Application, server


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--demo", action="store_true", required=True)
    p.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8765")))
    p.add_argument(
        "--host",
        default="127.0.0.1",
        help="Compatibility with managed preview; ignored outside --preview",
    )
    p.add_argument(
        "--preview",
        action="store_true",
        help="Internal cloud QA only; binds all interfaces",
    )
    args = p.parse_args()
    if os.name == "nt" and not os.environ.get("GTC_VERIFIED_D_VOLUME"):
        raise SystemExit(
            "Use scripts/launch.ps1 after verifying the intended D: volume."
        )
    app = Application(ROOT / "runtime/demo.sqlite")
    http = server(app, args.port, preview=args.preview)
    print(
        f"GTC fixture DEMO at http://127.0.0.1:{http.server_port}; no live/native connection",
        flush=True,
    )
    try:
        http.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        http.server_close()


if __name__ == "__main__":
    main()
