# Integrated foundation blueprint

Owner directed Codex to take over on 2026-11-03. This supersedes setup-only coding
restrictions, not trading activation or paid-service restrictions. Demonstrations
use isolated fictional fixtures; unresolved policy is never silently approved.

| Modules | Interfaces / files | Invariants and tests |
|---|---|---|
| M01/02 | services/core.py: decimal_value, utc, strict_loads; coordinator/contracts.py: validate_report | finite decimals, UTC, exact fields, Draft 2020-12 and semantic validation |
| M03 | data/scanner.py: scan; data/mexc.py: PublicClient.collect/candles | GET-only allowlist, bounded timeout/retry, source time, metadata units, frozen snapshots |
| M04 | features/baseline.py: completed_bars, ema, atr, regime, trigger, plan_prices, propose | 600 hourly bars, cutoff/availability, gaps, SMA/Wilder, slope, prior-20 extrema, expiry, rounding |
| M05 | bots/shared.md, role briefs, roster.json | genuine handed-off IDs; applied-profile evidence separate; Auditor outside council |
| M06/11 | coordinator/store.py: create_case, import_report, release, decide, export_case | unique ID/hash, fixed snapshot/version, server import stamps, private first reports, veto/dissent |
| M07-10 | paper/engine.py: admit, fill_entry, cancel, close_request, fill_exit, monitor, reconcile, backup | serialized reservation, Decimal costs/sizing, partial-fill protection, no reversal, recovery/latches |
| M12 | research/evaluation.py and experiment registry | failed trials retained, undefined metrics explicit, no promotion endpoint |
| M13 | services/api.py | loopback, Host/Origin/session checks, bounded strict imports, structured errors |
| M14 | apps/dashboard/{index.html,app.js,style.css} | seven screens, common state IDs, real import/export, six council members, fixture/stale/offline labels |
| M15/16 | scripts/, tests/, evidence/ | D-volume identity/write check, no C fallback, dependency lock, independent numerical and lifecycle tests |

SQLite BEGIN IMMEDIATE serializes mutations. Tables store snapshots, cases,
reports, decisions, orders, fills, positions, events, experiments and settings.
Primary keys plus canonical hashes reject changed-payload ID reuse. Protective
rules persist in each fill transaction. Orders and positions have separate states.
Cash = initial cash + realized gross P&L - fees - carrying costs. Marked equity adds
unrealized P&L; missing marks are unknown. Faults latch until reviewed, not midnight.
An independent monitor command uses persisted quotes without LLM dependencies.
No distributed failover is claimed; this is a local single-user prototype.

The initial executable mode is DEMO with fixture policy. Public collection is
read-only and cannot create orders. Imports remain non-executable. No Grok-control
API, real order adapter, paid model, public deployment or policy activation is
provided. All critical acceptance cases remain in the requirements matrix.
Native account evidence, approved paper policy, forward economics and measured
24/7 runtime remain separate acceptance gates.
