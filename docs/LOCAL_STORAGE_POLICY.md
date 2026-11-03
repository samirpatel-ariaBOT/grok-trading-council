# Local Windows storage requirement

Decision ID: DEC-LOCAL-D-001
Authority: current explicit owner request to use the portable D: drive whenever
this new project runs or stores project files locally.
Status: REQUIREMENT RECORDED. No Windows setup or drive verification has run.

## Location and fresh setup

Use `D:\GrokTradingCouncil` as the proposed new project root. Both Grok's backend
and Codex's dashboard must use this location in future Windows setup instructions,
launchers and application configuration. Keep the remote GitHub repository as the
shared source repository. Do not import any previous trading project or settings.

Proposed layout (paths are requirements, not directories already created):

| Directory under the root | Purpose |
| --- | --- |
| `repo` | Fresh Git checkout, source, tests, docs and dashboard assets |
| `runtime` | Machine-specific virtual environments and local runtime tools |
| `data` | Market snapshots, paper databases, SQLite WAL/SHM and checkpoints |
| `logs` | Application, worker and launcher logs |
| `artifacts` | Reports, exported evidence, research outputs and builds |
| `cache` | Project-controlled package, tool and application caches |
| `tmp` | Project-controlled temporary files and staging |
| `backups` | Local recovery copies, clearly distinguished from off-drive backups |

Exclude runtime state, secrets, caches, databases and backups from the public Git
repository. Git stores source and approved non-sensitive fixtures. Local copies
on this drive are not protection against loss of the whole drive.

## Required setup and startup behavior

1. Before creating project files, verify that D: is the owner's intended portable
   volume, writable, has sufficient space and supports the required filesystem
   operations. Record a stable volume identity and a project-root marker; the
   drive letter alone is insufficient. Do not format or migrate the drive.
2. Check the volume identity and root marker on each startup. If the drive is
   absent, read-only, full, mounted elsewhere or replaced, stop with a clear error.
   Never silently write the project to C:, the current working directory or a
   different disk. A letter change needs an explicit configuration update.
3. Resolve all project-controlled paths from one configured root. Refuse path
   traversal or junction/symlink redirection outside the verified project volume.
   Set project processes' temporary and cache paths under the root; do not change
   system-wide HOME, user profile or other unrelated environment settings.
4. Keep virtual environments, dependencies and frontend build outputs on D:.
   Rebuild machine-specific environments from dependency locks when moving to a
   different computer; do not promise that copied environments are executable.
5. Keep SQLite on a verified local filesystem. Test transactions, locking,
   checkpointing, crash recovery and consistent backups on the actual target
   drive before a paper ledger is enabled. Do not copy a live database alone as
   a guaranteed consistent backup.
6. On write failure, loss of the drive or loss of data freshness, stop admission
   of new paper actions and show an unhealthy state. Recovery must reconcile
   persisted state before restart; no alternate-disk fallback or invented fills.
   A removable drive does not itself provide durable 24/7 runtime.
7. Display the active runtime host, configured root, last successful persistence
   and storage health in operational status. The dashboard must not say that
   native Grok cloud bots are running on D: unless that has actually been proven.

## Boundaries

This policy covers project-owned files and controlled processes. Windows, installed
browsers, antivirus and other host software can still create system-managed files
on C:. Do not claim that every operating-system write has been relocated.

Native Grok bots use their provider's runtime. Choosing D: for a future Windows
backend/dashboard does not move Grok's cloud computers onto the user's drive or
verify a local-to-cloud bridge. A computer that sleeps, disconnects or loses its
drive cannot supply continuous local monitoring. Hosting and continuity remain
separate decisions; no paid services are authorized by this storage request.

## Required acceptance evidence before local runtime is called ready

- Normal startup stores all project-controlled outputs within the verified root.
- Missing, replaced, read-only and full-drive cases fail without C: fallback.
- Cross-volume paths and redirected directories are rejected before writes.
- Unplug/reconnect and restart tests on disposable paper fixtures preserve a
  truthful health state and reconcile the ledger; no tests use real orders.
- A consistent backup restores on the intended Windows environment.
- Backend and dashboard configuration agree on the same root and host identity.

These are future implementation requirements. None is marked tested by this file.
