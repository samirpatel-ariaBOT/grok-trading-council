# Local Windows storage requirement

Decision ID: DEC-LOCAL-D-001
Authority: Owner's explicit requirement to keep all project-controlled local storage on the verified portable D: volume.
Status: SOURCE HARDENED; PHYSICAL WINDOWS EXECUTION UNVERIFIED.

## Canonical checkout and storage

The integrated branch expects the Git checkout itself at **D:\GrokTradingCouncil**.
The earlier proposed \`D:\GrokTradingCouncil\repo\` subfolder is **not** the live launcher layout; do not move files there.

| Location | Responsibility |
| --- | --- |
| \`D:\GrokTradingCouncil\.project-id\` | Fixed identity marker: \`gtc-fresh-20261102\` |
| \`D:\GrokTradingCouncil\scripts\, services\, apps\, tests\, config\, README.md\` | Git-tracked source and dashboard |
| \`D:\GrokTradingCouncil\.venv\` | Isolated, machine-specific Python 3.12 environment (ignored by Git) |
| \`D:\GrokTradingCouncil\runtime\demo.sqlite\` | Fixture-only SQLite demo ledger; WAL and SHM in same directory |
| \`runtime\tmp\, runtime\pip-cache\, runtime\pycache\` | Project-controlled temporary and cache data |
| \`runtime\backups\` | Local consistent SQLite backups (NOT protection against whole-drive loss) |
| \`runtime\public_readonly\` | Explicit read-only public collection; not part of demo ledger |

Future logs, artifacts, and market data must remain inside the same verified project root. Do not introduce parallel project paths or reuse old trading systems. Runtime data, secrets and caches must remain excluded from the public repository.

## Startup and setup requirements

1. Independently inspect \`Get-Volume -DriveLetter D\` and \`Get-Partition -DriveLetter D | Get-Disk\` to verify the physical intended volume. Record its actual \`UniqueId\` out of band. Do not guess a volume ID.
2. Use \`scripts\launch.ps1 -ExpectedVolumeUniqueId '<verified ID>' -Setup\` to create/check the isolated Python 3.12 environment and install the versions in \`requirements-dev.lock.txt\`. This is a deliberate one-time dependency setup, not a normal application start. Package pins are not yet accompanied by cryptographic hashes.
3. Launch the existing **fixture-only** server with \`scripts\launch.ps1 -ExpectedVolumeUniqueId '<verified ID>'\`. Startup does not reinstall packages. \`-CollectPublic\` is optional, read-only network collection and must never be confused with the demo. It is not required for local demo acceptance.
4. The launcher rejects an incorrect/missing volume ID, wrong root/marker, unhealthy or non-NTFS/ReFS volume, insufficient free capacity, linked/reparse project output paths, wrong Python interpreter, and mismatched or unhealthy dependencies before starting the demo. It checks the path components it controls, but Windows volume identity and all OS behavior need physical testing.
5. The launcher chooses the same exact root for services and dashboard, and retains \`TEMP\`, \`TMP\`, \`PIP_CACHE_DIR\`, \`PYTHONPYCACHEPREFIX\`, and \`PYTHONNOUSERSITE\` only for its child processes. It does not change system-wide profiles or Windows directories. Host OS, browsers, and Python installation may still use C:.
6. Rebuild the environment with explicit owner review when moving between PCs. Do not copy a venv and assume it will work. Do not delete any existing environment without approval.
7. SQLite is for the fictional demo, on a locally mounted NTFS/ReFS volume only. Confirm transaction locking, persistence, backup/restore, restart recovery and healthy fail-closed behavior using **disposable fixture data** before claiming Windows durability.
8. On a missing, replaced, full, read-only or disconnected volume, do not redirect to C: or create an alternative ledger. Stop the fixture service and inspect/reconcile state before restarting.

## Practical acceptance evidence still required

- Run first-time setup, ordinary launcher startup, 85+ existing Python tests (actual Windows result recorded), and browse all seven dashboard screens on the intended laptop.
- Confirm a normal stop and restart preserves fixture events. Make a consistent backup using the existing backup script only after verifying its scope.
- Negative startup tests: wrong UniqueId, missing marker, wrong interpreter, incomplete venv, redirect/junction and insufficient space. Use isolated test conditions; never damage or disconnect an active volume to simulate a failure.
- Document host identity, path, Windows and Python versions, Volume UniqueId, dependency output, storage health, and any observed startup error.
- Explicitly distinguish source-level validation from a physical drive / removable-drive loss / Windows durability test.

## Boundaries

No exchange keys, live orders, paid APIs, hosting activation or live brokerage connection are authorized.
The native Grok bots run in provider infrastructure; putting project files on D: does not migrate cloud bots to the portable drive or establish 24/7 unattended operation. A PC that sleeps or loses its portable drive is not a durable service host.
