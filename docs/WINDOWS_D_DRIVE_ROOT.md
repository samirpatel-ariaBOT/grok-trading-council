# Windows portable D: drive and fixture demo

**Status: Windows and physical drive execution still NOT VERIFIED.** Source-only review and Linux tests do not certify the owner's laptop. The project checkout must be exactly `D:\GrokTradingCouncil` (not `D:\GrokTradingCouncil\repo`). Do not copy credentials or files from earlier trading systems. Do not format, migrate or disconnect the drive while GTC is running.

## Read-only preflight (owner's laptop)

```powershell
Get-Volume -DriveLetter D | Format-List DriveLetter,FileSystemLabel,FileSystem,UniqueId,HealthStatus,SizeRemaining
Get-Partition -DriveLetter D | Get-Disk | Format-List FriendlyName,SerialNumber,BusType,HealthStatus
Get-Content D:\GrokTradingCouncil\.project-id
py -0p
py -3.12 -c "import sys; print(sys.version); print(sys.executable)"
git -C D:\GrokTradingCouncil status --short
git -C D:\GrokTradingCouncil branch --show-current
git -C D:\GrokTradingCouncil rev-parse HEAD
```

Confirm the intended portable disk and UniqueId independently. Stop if the expected source or volume identity differs from your reviewed record. The source currently requires an NTFS/ReFS volume and at least 512 MiB available for setup, or 128 MiB for an ordinary start. Those thresholds are launcher preflight floors, not a full capacity estimate.

## Separate setup and fixture start

```powershell
cd D:\GrokTradingCouncil
$verifiedUniqueId = Read-Host 'Verified portable D: volume UniqueId'
.\scripts\launch.ps1 -ExpectedVolumeUniqueId $verifiedUniqueId -Setup
.\scripts\launch.ps1 -ExpectedVolumeUniqueId $verifiedUniqueId
```

Setup creates a Python 3.12 virtual environment only when needed, installs pinned developer packages, and checks dependency consistency. Normal start performs verification but **no pip install**. The script fails on mismatched volume, project marker, linked output path, interpreter or dependency versions. It does not automatically change execution policy. Run in a PowerShell console with an approved local script policy.

## Acceptance

Open `http://127.0.0.1:8765` on the same laptop only. The backend must return mode `DEMO`, `live_market_connected=false` and native status `REQUIRED_UNVERIFIED`. Check Overview, Meeting Room, Markets, Positions, Research, Journal and Settings. Use only fictional position actions; never connect real exchange accounts. The existing code intentionally offers no live-order endpoint.

In a second terminal:

```powershell
cd D:\GrokTradingCouncil
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts\check_setup.py
$state = Invoke-RestMethod http://127.0.0.1:8765/api/state
if ($state.mode -ne 'DEMO' -or $state.live_market_connected -ne $false -or
    $state.native_operations.status -ne 'REQUIRED_UNVERIFIED') {
    throw 'Unexpected mode. Stop.'
}
```

The old Linux test evidence reports 85 passes. Record the actual Windows result; the new source-contract tests do not simulate a real removable-drive failure or a true Windows launcher execution.

## Shutdown and recovery

Press Ctrl+C in the launcher terminal, wait for the prompt, and confirm no listener remains on port 8765:

```powershell
Get-NetTCPConnection -LocalPort 8765 -State Listen -ErrorAction SilentlyContinue
Get-ChildItem D:\GrokTradingCouncil\runtime -Filter 'demo.sqlite*'
```

Do not detach the drive before every GTC process has stopped. Test stop/restart persistence and SQLite consistent backup/restore on disposable fixture copies before declaring the D: deployment durable. Never manually remove SQLite WAL/SHM or overwrite an active ledger.

Python installation, Windows services, browsers, and native Grok cloud bots can use storage outside D:. Project-owned runtime paths, however, must remain within the verified project root. A portable drive is not a substitute for a 24/7 host.
