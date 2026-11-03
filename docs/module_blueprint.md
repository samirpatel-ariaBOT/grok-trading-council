HISTORICAL STARTER DOCUMENT — superseded for the current implementation by README.md, PROJECT_STATUS.md and docs/integrated_blueprint.md. Retained for traceability.

# Bootstrap blueprint — limited scope

This document covers only code present in starter 0.1.
Grok owns completing the full M01-M16 blueprint before substantive module work.
Codex contributes and leads the M14 frontend blueprint/implementation. Both agree
the M13/M14 boundary before integration. See docs/FRONTEND_HANDOFF.md.

## Setup configuration (preliminary part of M01/M02)
Path: `services/configuration/bootstrap.py`.
- `parse_bootstrap(text: str) -> BootstrapConfig`: strict JSON parser.
- `validate_bootstrap(value: Any) -> BootstrapConfig`: exact keys/types/constants.
- `load_bootstrap(path: Path) -> BootstrapConfig`: local UTF-8 input.
- `BootstrapConfig.report() -> dict[str, Any]`: setup status with readiness false.

Input: `config/bootstrap.json`, described by `schemas/bootstrap.schema.json`.
Only SETUP/PAPER/FIXTURE_ONLY with network, execution and paid use false is valid.
Duplicate properties, unknown/missing properties, wrong types, non-finite numbers,
foreign project identity and filled unresolved choices are rejected.
Errors are structured as ConfigurationError; CLI returns exit code 2.
There is no database, migration, reservation, order, external network call or retry.
There is no draft-policy approval/activation function yet. Do not call M01 complete.

## Environment setup (preliminary part of M15)
Path: `scripts/create_environment.py`.
`check_destination(root: Path) -> Path` verifies this project's marker and refuses
any existing environment. The command creates an isolated `.venv` with no pip or
third-party packages, then runs the setup checker and unit tests.
An incomplete environment remains visibly incomplete on failure; no silent
overwrite or deletion occurs. Existing unrelated environments are untouched.

## Diagnostic and evidence (preliminary part of M16)
`scripts/check_setup.py` prints configuration validity and explicit unready states.
`scripts/verify_bundle.py` checks the delivered source inventory, before edits.
Tests cover rejection of attempted activation, type coercion, duplicates,
malformed/unknown input, stale project identity, premature numeric defaults,
missing choices, CLI failure status and refusing to overwrite an environment.

## Remaining full-module map
All entries below require full design and implementation; a directory is not proof.

| ID | Responsibility | Proposed implementation location |
|---|---|---|
| M01 | Versioned config and reviewed policy activation | services/configuration/ |
| M02 | All task/report/plan/order/event schemas | schemas/, services/validation/ |
| M03 | MEXC metadata, candles, quotes and frozen snapshots | services/data/ |
| M04 | Exact numerical baseline and feature calculations | services/features/ |
| M05 | Seven distinct role instructions and verified bot identities | bots/ |
| M06 | Private first reports, challenge rounds and final decision | services/coordinator/ |
| M07 | Deterministic atomic admission and reservations | services/risk/ |
| M08 | Realistic paper order/fill lifecycle | services/paper/broker.py |
| M09 | Independent position monitoring and exits | services/paper/monitor.py |
| M10 | Authoritative ledger, recovery and reconciliation | services/paper/ledger.py |
| M11 | Timestamped evidence and bounded memory | services/evidence/ |
| M12 | Experiments, evaluation and reviewed promotion | research/ |
| M13 | Authenticated application interfaces and event delivery | services/api/ |
| M14 | Seven interactive screens | apps/dashboard/ |
| M15 | Operations, health, security, installation and usage | scripts/, docs/operations.md |
| M16 | Unit, integration, recovery and UI evidence | tests/, evidence/ |

The full requirements matrix still needs atomic requirements, source page/section,
implementation path, test ID, status and evidence path. Grok must recreate/expand it
from all five source documents and the newer confirmed decisions.
Do not mark the whole Stage 0 VERIFIED on the strength of this setup suite.

