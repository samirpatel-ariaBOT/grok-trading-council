"""Create a brand-new project venv. Do not install dependencies or contact services."""
from __future__ import annotations

import subprocess
import sys
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECT_ID = "gtc-fresh-20261102"


def check_destination(root: Path) -> Path:
    marker = root / ".project-id"
    if marker.read_text(encoding="utf-8").strip() != PROJECT_ID:
        raise ValueError("Wrong project marker; refusing setup.")
    destination = root / ".venv"
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(
            ".venv already exists. Use it only if it belongs to this new project; "
            "otherwise choose a fresh extraction directory. Nothing was replaced."
        )
    return destination


def main() -> int:
    if sys.version_info < (3, 12):
        print("BLOCKED: Python 3.12 or newer is required.", file=sys.stderr)
        return 2
    try:
        destination = check_destination(ROOT)
        destination.mkdir()  # Atomic refusal if another process created it.
        venv.EnvBuilder(
            system_site_packages=False, clear=False, with_pip=False
        ).create(destination)
        interpreter = destination / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
        commands = [
            [str(interpreter), "-I", "scripts/check_setup.py"],
            [str(interpreter), "-I", "-m", "unittest", "discover", "-s", "tests", "-v"],
        ]
        for command in commands:
            result = subprocess.run(command, cwd=ROOT, check=False)
            if result.returncode:
                return result.returncode
    except (OSError, ValueError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    print("Fresh environment created; bootstrap checks passed. Trading is not implemented.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

