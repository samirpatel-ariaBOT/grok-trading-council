# Verification · integrated foundation 0.2

Executed 3 November 2026 in the Linux cloud checkout. This is separate from the
owner's Windows PC and physical D: drive. Exact command results are retained in
`evidence/test_results.json`.

| Check | Actual result |
|---|---|
| `.venv/bin/python -m pytest -q` (resolved interpreter `/tmp/gtc-build-venv/bin/python`) | **85 passed**, exit 0 |
| `node --check apps/dashboard/app.js` | exit 0 |
| `ruff check services research tests/test_api.py tests/test_boundaries.py tests/test_foundation.py --select F` | all checks passed, exit 0 |
| Public MEXC ticker collector, one real request | **BLOCKED**, exit 2; HTTP 200 HTML “Site Unavailable”, not JSON |
| Uploaded v7 ZIP SHA256 | Matches owner-provided `68313dea…13ab55f` |
| Four PDF page-text comparison | All 46 pages match available combined v2; binary variants explicitly recorded |

## Scope of automated evidence

The 85 tests include the 19 original setup-boundary tests and 66 new foundation/API
checks. Tests cover strict JSON/numerical handling, actual seeded EMA values,
Wilder ATR, 600-bar gaps/UTC/availability, breakout boundaries, plan direction and
rounding, expiry, scanner/API errors, duplicate symbols, provenance, role schema,
import stamping/idempotency, WAIT and Guardian veto, concurrent slot admission,
post-rounding risk/notional, partial fills, pause/close, quote-gap fills, stale marks,
persistent latches, backup recovery, reconciliation, duplicate triggers, metadata,
research arithmetic, browser mutation authentication and actual loopback HTTP actions.

The v7 archived scripts are reference text, not imported by the test runner.
Numerical and protocol tests do not establish native-bot intelligence, profitability
or real exchange execution. Fee/funding/liquidity settings are fictional demo inputs.

## Browser observations

Managed preview could not launch the Python executable, so the supported static
preview route was used with an explicit **STATIC UI REVIEW** banner and immutable
fixture snapshot. The application HTML/CSS/JS are unchanged by that adapter.
Backend actions were independently exercised through actual HTTP integration tests.
No public application was deployed.

- All seven page headings rendered in desktop browser; visible labels separate
  fixture data, native status, execution authority and readiness.
- Meeting case selector changed to CASE-DEMO-VETO; displayed **SKIP / VETO
  PRESERVED**, correct snapshot, FINAL Chief/Guardian reports, and preserved dissent.
- Contract filter removed the unmatched row. Report selection was corrected to
  prefer the final report rather than lexicographic record order.
- A 390 × 844 iframe rendered the same app (375px content width after scrollbar).
  All seven screens measured `body.scrollWidth == body.clientWidth == 375` after
  correcting sidebar/grid overflow. Desktop measured 1348/1348.
- Screenshots: `evidence/ui/gtc-desktop-review-final.jpg` and
  `evidence/ui/gtc-mobile-review-final.jpg`.

Not yet verified: exhaustive loading/empty/stale/partial/error/disconnected behavior
on every screen, full accessibility audit, Windows launcher execution, actual D:
identity, native bot configuration, native group, automatic delivery, real live feed,
24-hour unattended runtime/alert evidence, performance under production load, or
out-of-sample economic results. These remain PARTIAL/BLOCKED in the 107-row matrix.

## Publication limit

The large PDF upload did not complete. This source branch excludes the four binary
PDFs and records their expected paths/hashes in spec/SOURCE_INDEX.json. Full extracted
text, master instructions, all executable source/tests and UI screenshots are included.
The earlier complete local checkpoint retains the PDFs.

## Reproduction

Create an isolated environment, install `requirements-dev.lock.txt`, then run the
commands above. Use `scripts/run.py --demo` for the real local API + dashboard.
`python scripts/build_ui_preview.py` generates the static QA-only snapshot.
`scripts/update_manifest.py` records source hashes and `scripts/verify_bundle.py`
checks them. Source integrity does not certify operational readiness.
