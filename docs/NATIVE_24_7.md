# Native Grok operations requirement

The owner explicitly requires the existing seven native Grok bots to perform their
assigned duties around the clock. `config/native_operations.json` records the
design targets and evidence required. Codex asked Grok to inspect and configure
supported account-side routines in issue #1, request GTC-NATIVE-24X7-001.

This repository cannot create, wake or control a native Grok profile. No supported
native-control bridge has been demonstrated. The hourly task identifier in the
manifest is owner/Grok-reported history, not a current account inspection.
Consequently the dashboard must say **Required / unverified**, never “live 24/7”.

The intended pattern is a continuously available data/position service with native
specialists invoked on bounded cases and scheduled duties. Keeping an LLM thinking
every second is neither necessary nor proof of continuous market protection.
Native scheduler limits, allowance, dispatch, persistence and alert delivery must
be measured in the actual account. Do not automate the website by scraping sessions,
evade quota limits, silently substitute API agents, or create duplicate routines.

Every native job needs job ID, role, case/snapshot IDs, scheduled/start/finish UTC,
result/error, retry count, instruction version and available quota evidence.
Timeouts produce WAIT; stale quotes or missed independent-monitor deadlines block
new entries. Native group chat remains unverified. Manual JSON import is a useful
development bridge and **does not satisfy unattended operation**.

An always-on local computer would have to keep the verified D: volume connected,
power/sleep/network configured and restart supervision proven. Grok cloud storage
is separate from D:. No durable host or 24-hour successful run has been verified.
The fixture application can be built and tested while these account/runtime gates
remain open; operational activation remains disabled.
