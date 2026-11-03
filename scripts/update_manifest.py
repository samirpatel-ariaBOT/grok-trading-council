"""Record tracked and new non-ignored source files; excludes the manifest itself."""

from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]
if __name__ == "__main__":
    paths = (
        subprocess.check_output(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
            cwd=ROOT,
        )
        .decode()
        .split("\0")
    )
    hashes = {
        name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
        for name in sorted(set(paths))
        if name
        and name != "BUNDLE_MANIFEST.json"
        and (ROOT / name).is_file()
        and not (ROOT / name).is_symlink()
    }
    (ROOT / "BUNDLE_MANIFEST.json").write_text(
        json.dumps(
            {
                "version": "integrated-foundation-0.2",
                "purpose": "Source integrity only; not operational readiness",
                "sha256": hashes,
            },
            indent=2,
        )
        + "\n"
    )
    print(f"Recorded {len(hashes)} source files")
