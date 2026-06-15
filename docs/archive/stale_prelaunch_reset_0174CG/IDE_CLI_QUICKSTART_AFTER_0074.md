# IDE/CLI Quickstart - After TASK_CONTENTOPS_0074

LOCAL ONLY | NO NETWORK | NO PROVIDER | NO PLATFORM | NO CREDENTIALS

Short operational guide for a local IDE/CLI worker. Run everything from the repo
or use `git -C` with the absolute repo path.

## Repo path
A:\Capital Chronicle\tools\cc-live-contentops

## First commands (orient)
- git -C "A:\Capital Chronicle\tools\cc-live-contentops" status --short
- git -C "A:\Capital Chronicle\tools\cc-live-contentops" log --oneline --decorate -5
- python -m live_contentops.cli status

## Status / summary commands (read-only)
- python -m live_contentops.cli alpha-wait-state-summary
- python -m live_contentops.cli ide-cli-document-bundle-summary
- python -m live_contentops.cli real-artifact-pipeline-trace-summary

## Test commands
- python -m pytest -q
- python -m pytest -q tests/test_alpha_wait_state.py

## Safe read-only inspection
- Read docs under docs/ (start with IDE_CLI_DOCUMENT_BUNDLE_AFTER_0074.md).
- Read live_contentops/*.py modules.
- Use search/read tools rather than executing code that touches the network.

## Hard rules
- Use `git -C "A:\Capital Chronicle\tools\cc-live-contentops"` if your terminal
  starts in a sibling repo.
- Never run `git add .` — stage explicit paths only.
- Never edit, stage, or commit `.gitignore` (operator-owned drift).
- Never read env files or credentials.
- Never make network/provider/search/platform calls.
- Never modify the sibling cc-contentops repo or the Capital Chronicle core repo.

## Closing a task
Use the evidence packet template in
docs/IDE_CLI_EVIDENCE_PACKET_TEMPLATE_AFTER_0074.md.
