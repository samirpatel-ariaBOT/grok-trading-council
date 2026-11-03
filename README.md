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

## Start on the intended portable D: drive

1. Put this fresh branch's checkout at **D:\GrokTradingCouncil**. Do not reuse another
   project's directory or data. Do not format or migrate the drive.
2. In PowerShell, inspect `Get-Volume -DriveLetter D | Format-List DriveLetter,FileSystemLabel,UniqueId,HealthStatus`.
3. Confirm that this is the intended portable volume, then run:

```powershell
cd D:\GrokTradingCouncil
.\scripts\launch.ps1 -ExpectedVolumeUniqueId '<the verified UniqueId>'
```

The launcher checks the root, volume identity, write access and linked directories;
it keeps the environment, project temp files, cache and SQLite data under D:.
It stops rather than falling back to C:. The Python installation and operating-system
storage are outside this project's storage guarantee. Windows execution and the
physical volume have **not** been verified from this cloud environment.

Open **http://127.0.0.1:8765** after the launcher prints its ready message. The demo
clock advances only when you select **Advance demo 1s**. Requesting a close records
intent first; the next step supplies the fictional quote and exit fill.

## Linux/cloud development

This is separate from the owner's physical D: drive:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.lock.txt
.venv/bin/python -m pytest -q
.venv/bin/python scripts/run.py --demo
```

`python scripts/collect_public.py` makes one public read-only discovery request and
stores immutable raw bytes under `runtime/public_readonly/`. It never sends data
into the demo ledger. The observed request from this cloud returned HTML “Site
Unavailable”; the collector blocked it. Successful live collection is not claimed.

`python scripts/monitor_demo.py --quotes <fictional-quote-map.json>` runs the
independent demo monitor. It uses actual UTC, so a frozen fixture's old timestamps
will correctly become stale. This is a development command, not a durable host or
24/7 readiness claim. `python scripts/backup_demo.py` makes an integrity-checked
SQLite backup. Never replace an active ledger with a backup while the app runs.

## Review map

- [Current status and remaining gates](PROJECT_STATUS.md)
- [Module blueprint](docs/integrated_blueprint.md)
- [Native 24/7 duties and acceptance evidence](docs/NATIVE_24_7.md)
- [Native operations manifest](config/native_operations.json)
- [Shared brief and seven role files](bots/shared.md)
- [Report/import contract](docs/REPORT_CONTRACT.md)
- [Requirements matrix](docs/requirements_matrix.csv)
- [Verification report](evidence/verification.md)
- [Source inventory and PDF hash differences](spec/SOURCE_INDEX.json)
- [Master instructions](spec/originals/Grok_Trading_Council_Master_Build_Instructions.txt) and [full 46-page text](spec/text/project_v2.txt)

The four original PDFs contain all 46 pages, including the seven screen concepts.
Their large binary upload did not complete. They remain in the verified local
checkpoint; this branch includes full extracted text, master instructions and
dashboard screenshots. It does not claim the original PDFs are uploaded.
Their extracted page text matches the available combined v2 document. Parts 1 and
4 differ in binary hash from Grok's earlier reported hashes; the inventory records
this explicitly. The supplied v7 ZIP hash was verified. Its incompatible scripts
are retained byte-for-byte as non-executable reference text in `evidence/upstream_v7/`.
The canonical implementation is under `services/`; do not import those old variants.

## Collaboration

[Issue #1](https://github.com/samirpatel-ariaBOT/grok-trading-council/issues/1)
continues engineering coordination. Grok's draft PR #2 is preserved. Codex's
integrated foundation is a separate branch. A GitHub notification is not proof
that Grok woke, read it, or configured a native routine. No automatic merge.

Schema 3.0 is implemented and locally tested but still awaiting Grok's independent
integration review. Operational family/directions, financial policy, usage allowance,
native scheduling, durable runtime and forward evaluation are unresolved gates.
The demo's example limits are fictional test inputs, not accepted operating policy.
