# Grok Trading Council

An editable seven-screen dashboard and deterministic **fixture-only paper demo**
for the fresh GTC project. Native Grok Bots is the selected analysis route.
The owner requires native bots to operate 24/7; that account/runtime capability
is **required but unverified**, and this application does not pretend to provide it.

**Stage 0: IN_PROGRESS. No live orders, paid API route, public app deployment or
operational trading activation.** The repository is public by the owner's decision.

## What runs now

- Canonical Decimal EMA50/200, Wilder ATR14, completed-bar breakout and bounded plan.
- Strict public discovery validation plus a bounded, provenance-preserving HTTP collector.
- Version 3.0 report schema, operator-stamped manual imports, frozen cases, bounded
  first/challenge rounds, WAIT and veto-preserving decisions.
- Atomic SQLite demo admission, reservations, partial entry/exit fills, fees,
  executable marks, gap exits, pause, reconciliation, backup and an independent
  demo monitor command. Every engine path rejects non-fixture execution.
- Overview, Meeting Room, Markets, Positions, Research, Journal and Settings.
  The local application uses actual demo ledger records. Reports and prices are
  explicitly fictional. It has no native bot-control or exchange-order endpoint.

## Start on the intended portable D: drive (Windows)

The **Git checkout itself**, not a \`repo\` subfolder, must be at
\`D:\GrokTradingCouncil\`. Never move or format unrelated drive content.

First inspect the physical disk and confirm this is your intended portable drive:

\`\`\`powershell
Get-Volume -DriveLetter D | Format-List DriveLetter,FileSystemLabel,FileSystem,UniqueId,HealthStatus,SizeRemaining
Get-Partition -DriveLetter D | Get-Disk | Format-List FriendlyName,SerialNumber,BusType
py -0p
py -3.12 -c "import sys; print(sys.version)"
\`\`\`

Verify the disk/UniqueId independently. Do not use a guessed value. In PowerShell
from the reviewed integrated checkout:

\`\`\`powershell
cd D:\GrokTradingCouncil
$expected = Read-Host 'Enter the verified D: volume UniqueId'
.\scripts\launch.ps1 -ExpectedVolumeUniqueId $expected -Setup
.\scripts\launch.ps1 -ExpectedVolumeUniqueId $expected
\`\`\`

Setup runs **only** with \`-Setup\`; it may create \`.venv\` and install the exact
versions pinned in \`requirements-dev.lock.txt\`. The pins currently lack
cryptographic package hashes. Normal startup **does not reinstall packages**.
If a PowerShell execution policy blocks the script, follow your locally reviewed
execution-policy process; do not bypass security settings automatically.
The launcher refuses volume/root/marker mismatches, linked project output paths,
unhealthy or inadequate storage, missing/bad venv, and incompatible Python.
It does not change system-wide profile locations. Physical Windows verification
is still **unperformed**.

When the fixture server reports
\`GTC fixture DEMO at http://127.0.0.1:8765; no live/native connection\`,
open **http://127.0.0.1:8765** locally on that same computer.
Do not enable the cloud preview or expose port 8765 on a network.

### Windows fixture-only acceptance checks

In a **second PowerShell** window:

\`\`\`powershell
cd D:\GrokTradingCouncil
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts\check_setup.py
$state = Invoke-RestMethod http://127.0.0.1:8765/api/state
if ($state.mode -ne 'DEMO' -or $state.live_market_connected -ne $false -or
    $state.native_operations.status -ne 'REQUIRED_UNVERIFIED') {
    throw 'Unexpected mode or native status: stop the server'
}
$state | Select-Object mode,stage,fixture_clock,live_market_connected
\`\`\`

In the browser verify each screen:
**Overview, Meeting Room, Markets, Positions, Research, Journal, Settings**.
They must show fictional fixtures and blocked native/operational activation.
The demo clock advances only by clicking **Advance demo 1s**. Requesting a
fictional position close records intent; the next demo step supplies the exit
quote and fill. Inspect the journal/ledger after this action.
Save actual command exit codes and screenshots; the prior 85-test Linux run
and static UI checks do not establish Windows operation.

For orderly shutdown, press **Ctrl+C** in the launcher's PowerShell window.
Wait for the command prompt to return and check that no service is listening:

\`\`\`powershell
Get-NetTCPConnection -LocalPort 8765 -State Listen -ErrorAction SilentlyContinue
Get-ChildItem D:\GrokTradingCouncil\runtime -Filter 'demo.sqlite*'
\`\`\`

Do not detach D: while any fixture process is running. Never manually delete
SQLite WAL or SHM files. Confirm stop/restart persistence and backup integrity
before calling the portable-drive runtime ready.

## Linux/cloud development (NOT Windows verification)

\`\`\`sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.lock.txt
.venv/bin/python -m pytest -q
.venv/bin/python scripts/run.py --demo
\`\`\`

\`python scripts/collect_public.py\` makes one optional public read-only discovery
request and stores raw provenance under \`runtime/public_readonly/\`. It never
feeds the demo ledger. The observed cloud request returned HTML "Site Unavailable";
successful live collection is not claimed.

\`python scripts/monitor_demo.py --quotes <fictional-quote-map.json>\` runs the
independent demo monitor with actual UTC quote timestamps. It is not a durable
24/7 service. \`python scripts/backup_demo.py\` creates an integrity-checked
SQLite backup. Never replace an active ledger with a backup.

## Review map

- [Current status and remaining gates](PROJECT_STATUS.md)
- [Module blueprint](docs/integrated_blueprint.md)
- [Native 24/7 duties and acceptance evidence](docs/NATIVE_24_7.md)
- [Native operations manifest](config/native_operations.json)
- [Shared brief and seven role files](bots/shared.md)
- [Report/import contract](docs/REPORT_CONTRACT.md)
- [Requirements matrix](docs/requirements_matrix.csv)
- [Verification report](evidence/verification.md)
- [Local Windows storage policy](docs/LOCAL_STORAGE_POLICY.md)
- [Source inventory and PDF hash differences](spec/SOURCE_INDEX.json)
- [Master instructions](spec/originals/Grok_Trading_Council_Master_Build_Instructions.txt) and [full 46-page text](spec/text/project_v2.txt)

The four source PDFs contain 46 pages, but their large binary GitHub upload
did not complete. The integrated branch includes extracted text, master
instructions and screenshots; it does not claim the PDFs are in GitHub.
Parts 1 and 4 differ in binary hash from Grok's earlier reported hashes.
Archived v7 scripts are non-executable references in \`evidence/upstream_v7/\`;
do not import their incompatible implementations.

## Collaboration and operational boundary

[Issue #1](https://github.com/samirpatel-ariaBOT/grok-trading-council/issues/1)
coordinates review. PR #2 remains preserved and this integrated PR remains
separate. GitHub notifications do not prove native bot activation.
Schema 3.0, operational instrument scope, risk policy, usage allowance, native
24/7 execution, forward evaluation and durable host remain unresolved.
The fixture demo's example limits are not approved financial policy.
