"""Source-contract checks for the Windows fixture launcher.

These checks do not pretend to execute PowerShell or touch the owner's D: drive.
Actual Windows/portable-volume acceptance is required separately.
"""
from pathlib import Path
import os
import re

import pytest

ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "scripts" / "launch.ps1"


def test_windows_launcher_source_fail_closed():
    source = LAUNCHER.read_text(encoding="utf-8")
    required = (
        "ExpectedVolumeUniqueId",
        "Get-Volume -DriveLetter D",
        "UniqueId -cne $ExpectedVolumeUniqueId",
        "gtc-fresh-20261102",
        ".project-id",
        "Assert-LocalPath",
        "[IO.FileAttributes]::ReparsePoint",
        "runtime\\demo.sqlite",
        "runtime\\demo.sqlite-wal",
        "runtime\\demo.sqlite-shm",
        "Python 3.12",
        "py -3.12 -m venv",
        "PYTHONPYCACHEPREFIX",
        "PIP_CACHE_DIR",
        "PYTHONNOUSERSITE",
        "pip check",
        "requirements-dev.lock.txt",
        "scripts\\run.py --demo",
    )
    for phrase in required:
        assert phrase in source, f"missing Windows fail-closed contract: {phrase}"
    assert "py -3 -m venv" not in source
    assert not re.search(r"scripts\\run\.py\s+--preview", source)
    assert "C:\\GrokTradingCouncil" not in source


def test_setup_install_is_explicitly_gated():
    source = LAUNCHER.read_text(encoding="utf-8")
    assert "if ($Setup) {" in source
    assert "if ($Setup) {\n    & $ProjectPython -m pip install" in source
    assert "if ($Setup) {\n    Write-Host" in source
    assert "exit 0" in source


def test_docs_match_actual_root_and_demo_only():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    policy = (ROOT / "docs" / "LOCAL_STORAGE_POLICY.md").read_text(encoding="utf-8")
    assert "D:\\GrokTradingCouncil" in readme
    assert "D:\\GrokTradingCouncil" in policy
    assert "repo subfolder" not in readme.lower()
    assert "fixture-only" in readme.lower()
    assert "24/7" in policy
    assert "Windows" in policy


@pytest.mark.skipif(os.name != "nt", reason="requires actual Windows PowerShell environment")
def test_windows_shell_parser_when_available():
    import subprocess
    if not shutil_which_pwsh():
        pytest.skip("PowerShell 7 not installed on this Windows host")
    command = (
        "$tokens=$null;$errors=$null;"
        "[System.Management.Automation.Language.Parser]::ParseFile("
        "'scripts/launch.ps1',[ref]$tokens,[ref]$errors)|Out-Null;"
        "if($errors.Count){$errors|Out-String|Write-Error;exit 1}"
    )
    subprocess.run(["pwsh", "-NoProfile", "-Command", command], cwd=ROOT, check=True)


def shutil_which_pwsh():
    import shutil
    return shutil.which("pwsh")
