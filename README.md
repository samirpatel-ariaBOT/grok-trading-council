# Grok Trading Council — fresh setup 0.1

Prepared 2 November 2026 for Samir Patel.

This is the fresh project bootstrap, not the completed trading platform. It contains
new setup code, a strict non-executing configuration, tests, and collaboration
instructions. No earlier trading project's code, databases, credentials, numerical
defaults, strategy implementation, or Git history has been imported.

## Start

1. Read `docs/START_HERE.md`.
2. Verify the original handover: `python -I scripts/verify_bundle.py`.
3. Create an isolated environment: `python -I scripts/create_environment.py`.
   Python 3.12+ is required. On Windows use `py -3.12` in place of `python`.
4. The setup script runs configuration checks and the bootstrap test suite.
5. Attach the accompanying Grok instruction file and this ZIP to the current Grok
   project containing the original four PDFs and master instructions.

No third-party packages are needed by this bootstrap. It does not install pip,
download packages, start services, call an exchange, create bots, or place trades.

## Source documents

The five existing specification files are required in addition to this package.
Their names and expected page coverage are in `spec/SOURCE_INDEX.json`.
The PDFs and full-resolution visuals are NOT duplicated in this small ZIP.
Grok must import the exact current-project files into the new repository and
record their actual hashes and visual inventory. Do not reconstruct them from memory.

## Current scope

- MEXC crypto futures; discover all eligible contracts.
- Paper/demo development only.
- Seven separately configured roles; Chief, Scout, News, Sentiment, Quant and
  Guardian form the council, with Research Auditor outside it.
- Seven screens using the supplied visual concepts.
- Conventional software owns calculations, admission, execution simulation,
  position protection and the ledger.

Contract settlement/family, directions, agent route, numerical risk policy,
timeframes, usage budget and runtime host are not activated by this bootstrap.
USDT perpetuals, long/short and the original PDF defaults are working proposals
to resolve explicitly, not settings recovered from another project.

## Status and evidence

See `PROJECT_STATUS.md` and `evidence/`.
A successful setup check means only that this bootstrap is valid.
It does not certify data access, economic performance, bot creation, full M01,
a working broker, UI, independent monitoring, or continuous operation.

## Collaboration

Read `AGENTS.md` and `docs/COLLABORATION_PROTOCOL.md`.
Grok should supply its own architecture advice and challenge Codex proposals.
Codex leads the editable seven-screen interface; Grok leads the bots/backend.
Both agree the data contract and review each other's work. Read
`docs/FRONTEND_HANDOFF.md` for this updated division of work.
Resolve engineering choices using reproducible evidence. Keep the owner's decisions
about spending, credentials, scope and real-money operation explicit.
