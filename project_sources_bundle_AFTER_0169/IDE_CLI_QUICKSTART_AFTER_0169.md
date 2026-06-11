# IDE CLI Quickstart (After 0169)

- Repo path: A:\Capital Chronicle\tools\cc-live-contentops
- Expected baseline: 444ef2c

## Safe Validation Commands
- `python -m pytest -q`
- `python -m live_contentops.cli status`
- `python -m live_contentops.cli pre-alpha-institutional-pre-antigravity-static-qa-hardening-summary`
- `node --check ui/institutional_shell/app.js`
- `git status --short`
- `git diff --check`

## Hard Boundaries
- No env/API/browser unless explicitly scoped.
- No `git add .`
- No Project Sources refresh from Cline directly (operator manual upload).

## Bundle Verification
Check `BUNDLE_FILE_LIST_AFTER_0169.txt` matches actual contents in `project_sources_bundle_AFTER_0169/`.
