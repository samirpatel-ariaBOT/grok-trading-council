# Report contract 3.0 · implemented proposal for joint review

The canonical schema is `schemas/report.schema.json`, JSON Schema Draft 2020-12.
Version 2.0 from the v7 archive remains historical reference, not an active parser.
Do not silently relabel old reports: adapt them explicitly and retain their original
bytes/provenance. Grok's independent agreement is still outstanding.

Every role report contains report/case/snapshot IDs, canonical role and bot ID,
instruction/strategy/policy versions, UTC creation timestamp, INITIAL or FINAL phase,
summary, provenance, missing-evidence list, dissent list and `non_executable: true`.
Each role has a distinct required payload; unknown fields are rejected. Source
availability must not exceed the case cutoff. Context IDs must match exactly.
Numeric contract values elsewhere use finite decimal strings; Python booleans are
never numbers. Supported numerical magnitude is zero or 1e-30 through 1e30.

`POST /api/import` accepts only `{ "operator": "...", "report": {...} }` under the
local session token. The service adds importer, import time, content SHA256 and
operator-attested origin. The role label and bot ID do not authenticate the native
sender. Imported source text is data, never instructions for the application.

Same report ID + identical payload returns the original stored envelope. A changed
payload under that ID is rejected. Each role gets one INITIAL and one FINAL record;
there is no unbounded repair/clarification loop. Six INITIAL reports must arrive
before release; the numerical proposal and hash then freeze. Final Chief and
Guardian reports must reference that hash. Missing mandatory evidence => WAIT;
any Guardian VETO => SKIP with the veto and dissent preserved. REDUCE is not an
approval: a revised case/plan and fresh review are required. Finalisation records
an auditable decision but never calls admission or places an order.

The local session token and loopback Host/Origin checks protect browser mutations.
This is a single-user local prototype, not multi-user authentication or security
isolation from other processes under the same operating-system account.

## Interfaces

| Method | Path | Behavior |
|---|---|---|
| GET | /api/state | Unified seven-screen read model; explicit fixture/native status |
| GET | /api/export | Non-executable case/report/decision/event evidence |
| POST | /api/case | New labelled review fixture from an immutable source snapshot |
| POST | /api/import | Validate, stamp and store one report; no order side effect |
| POST | /api/release | Require six first reports; freeze conventional proposal hash |
| POST | /api/decide | Apply bounded protocol and store decision; no order side effect |
| POST | /api/pause | Block entries and cancel pending remainder; preserve positions |
| POST | /api/close | Record close request; no immediate fill |
| POST | /api/demo-step | Advance fictional clock and process pending demo exits |
| POST | /api/experiment | Persist research draft; cannot activate |
| POST | /api/settings | Persist unapproved review note; cannot activate |

Errors return a stable `error` code and optional detail with HTTP 400/403/404.
Malformed JSON, duplicate fields and non-finite numbers are rejected before mutation.
Max import request is 256 KiB. Static assets have a fixed allowlist; arbitrary file
paths, credentials, account connections and live-order routes are not supported.

Run `python -m pytest tests/test_foundation.py tests/test_boundaries.py tests/test_api.py -q`
for schema examples and positive/negative import, stamping, idempotency and veto tests.
