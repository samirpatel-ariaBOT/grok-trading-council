HISTORICAL STARTER DOCUMENT — superseded for the current implementation by README.md, PROJECT_STATUS.md and docs/integrated_blueprint.md. Retained for traceability.

# Frontend ownership and integration handover

Updated 2 November 2026. This is a work allocation and integration checklist.
No interface implementation is included in the current setup release.

## Ownership
Codex leads M14: design implementation and editing of all seven screens from this
side, in editable source under `apps/dashboard/`. Scope includes components,
layout, bot cards, charts, interaction states, accessibility and responsive behavior.
The preferred frontend approach is React/TypeScript, subject to the actual build
environment and joint blueprint; no dependency/framework version is activated here.

Grok leads the bot/backend implementation within the agreed stages, and gives
its own recommendations about the UI. Grok should question layouts, data assumptions
and workflows when evidence suggests improvements. Codex must answer that feedback.

Both own the contract between M13 and M14. Each assistant can review both sides.
A task owner coordinates changes rather than excluding the other's advice.

## Sources and seven screens
Use the current project's visual concepts and written screen contracts:
Overview, Meeting Room, Markets, Positions, Research, Journal, Settings.
Map requirements from PDF pages 38-45, retaining provenance and full-resolution
reference assets. The six-seat council excludes Research Auditor, whose work is
visible through its own role/research views.
The screen must remain editable components; a full-page image is a design reference.

## What Grok must deliver for frontend development
Before integration, propose a versioned contract with:
- Schemas, field units, enums, IDs and null/unknown semantics.
- Mode, source timestamp, receipt time, freshness and health status.
- Bot identities/status and supported capabilities.
- Cases, reports, decisions, risk reasons, orders/fills and ledger-backed positions.
- Research runs, journal exports and non-secret configuration.
- Read operations and each actually supported control operation.
- Structured errors, request/correlation IDs, authentication and authorization.
- Reconnect behavior, ordering/cursors and snapshot recovery for event delivery.
- Idempotency/version rules for mutations, and disabled reasons for unavailable controls.
- Labelled normal, empty, stale, partial, error and disconnected examples.

Use the project's proposed operation names only after agreement. Do not invent
provider APIs, a control bridge or native-bot automation that has not been observed.
The financial state and policy checks remain in the backend.

## How Codex can proceed before the backend
After its screen blueprint/source review, Codex can implement fixture-backed
components and a mock adapter using the agreed contract. All example data must be
visibly marked DEMO/FIXTURE; unavailable controls show why they are disabled.
A successful mock must never be reported as a successful backend action.
Connect the real adapter only when the service contract and authentication are tested.

## Branch and review arrangement
Codex works in `codex/ui-<task>`; Grok uses its own backend branch.
Discuss interface/schema changes in the shared integration issue before edits.
Grok proposes UI fixes and feedback through review comments or an agreed PR.
Do not overwrite the other branch, replace the whole dashboard, or silently
change a schema consumed by another module.
If both assistants share the owner's GitHub identity, label the source of comments
honestly and observe GitHub's actual review restrictions.

## Acceptance evidence
- Screen-by-screen requirement coverage, not just a polished landing screen.
- Desktop 1440px and phone 390px screenshots plus keyboard/reduced-motion checks.
- Loading, empty, stale, partial, error and disconnected behavior.
- Actual bot/decision details when selected; traceable source and execution state.
- Integration tests that compare UI state with the backend/ledger.
- Realistic controls, including MANUAL IMPORT when the automatic bridge is unsupported.
- No financial calculation or policy bypass implemented solely in the browser.

This work allocation does not enable live trading, paid services, public deployment,
or automatic assistant-to-assistant wake-up.

