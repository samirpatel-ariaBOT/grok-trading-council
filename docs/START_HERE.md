HISTORICAL STARTER DOCUMENT — superseded for the current implementation by README.md, PROJECT_STATUS.md and docs/integrated_blueprint.md. Retained for traceability.

# Setup instructions

This package supplements the current project's five specification files.
It is a development foundation, not an installable trading application.

Recommended shared workflow: ask Grok to complete sections 3-4 first. Then clone
the new repository into a new local directory and run section 2 there. If you want
an offline check before the repository exists, sections 1-2 also work from the ZIP.
The assistant's workspace, Grok's computer and your computer are separate systems.

## 1. Fresh local directory
Use a new, empty directory. Suggested Windows location:
`%USERPROFILE%\Projects\grok-trading-council`.
On macOS/Linux: `~/Projects/grok-trading-council`.

If that name already contains work, choose a different new directory.
Do not extract into an old project or copy an old virtual environment.
The ZIP contains one top-level `grok-trading-council` folder. Avoid nesting it twice.

## 2. Python and the offline bootstrap
Python 3.12 or newer is required. The code was tested with Python 3.12.14 on Linux.
Use an existing compatible base Python installation, or install Python from
https://www.python.org/downloads/ if it is unavailable. A new isolated environment
will be created; no old project's packages are copied.

Windows PowerShell, from the newly extracted project folder:

```powershell
py -3.12 -I scripts/verify_bundle.py
py -3.12 -I scripts/create_environment.py
```

macOS/Linux, from the new project folder:

```sh
python3 -I scripts/verify_bundle.py
python3 -I scripts/create_environment.py
```

The setup command creates `.venv`, runs the setup diagnostic, then runs the
bootstrap tests. It does not download dependencies or start a background process.
It deliberately refuses to overwrite an existing `.venv`.

For subsequent checks, reuse only this new project's environment:

Windows:
```powershell
.\.venv\Scripts\python.exe -I scripts/check_setup.py
.\.venv\Scripts\python.exe -I -m unittest discover -s tests -v
```

macOS/Linux:
```sh
./.venv/bin/python -I scripts/check_setup.py
./.venv/bin/python -I -m unittest discover -s tests -v
```

Expected setup report: `BOOTSTRAP_VALID_ONLY`, `trading_ready: false`.
The process ends normally; there is no trading service to stop.

## 3. New private repository
Suggested name: `grok-trading-council`.
Use the owner's intended GitHub account. The account observed in this chat was
`samirpatel-ariaBOT`; Grok must verify its own authenticated account.
Create a brand-new PRIVATE repository with a README. Do not use an old project
as a template or import its Git history. If this name already exists, choose
a new unused name and report it.

Grok should do this through its supported GitHub tools if available.
Manual fallback:
1. Open https://github.com/new.
2. Select the intended owner and an unused repository name.
3. Select Private and initialize a README.
4. Create the repository.
5. Authorize the relevant GitHub connections to access this specific repository.
6. Send its exact URL to Grok and Codex.

A GitHub account being connected does not establish access to every new repository.

## 4. Import and collaboration
Grok clones the new repository into a new directory, creates `grok/bootstrap`,
imports this package at the repository root, and adds the current-project five
source documents under `spec/originals/`. Preserve the PDFs' original quality.
Extract their seven design assets without recompression if supported.

Verify the bundle BEFORE editing starter files. Then use Git commit hashes to
identify subsequent versions; the original bundle manifest is not a live CI gate.
Commit source and tests, not `.venv`, credentials or runtime state.
Grok opens a PR and the draft issues in `docs/initial_github_tasks/`.
Do not enable paid CI, hosting or automatic scheduled work during bootstrap.

Return: repository URL, branch, commit SHA, PR/issue links, commands run, test
results, unresolved decisions and Grok's own architecture recommendations.

## 5. Work from each side
Codex's initial implementation is this package. Once the new repository is
accessible, Codex can review the imported files and post concrete review comments.
Grok owns source intake and Stage 0 correction before other implementation.
Codex will lead the editable seven-screen dashboard from this side. Grok will
lead the bots/backend and supply its own UI suggestions. Both agree typed data
contracts and integration tests. See docs/FRONTEND_HANDOFF.md.
Agree task ownership in GitHub before both assistants edit the same module.

A supervised exchange works by asking each assistant to read the newest issue/PR
comments and respond. Automatic wake-up requires a separately tested integration;
no such integration is installed by this package.

## Reference documentation
Verified 2 November 2026:
- Python virtual environments: https://docs.python.org/3.12/library/venv.html
- GitHub repository creation: https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-new-repository
- GitHub PR reviews: https://docs.github.com/en/pull-requests/reference/pull-request-reviews
- Grok connectors: https://docs.x.ai/grok/connectors

