# IDE/CLI Quickstart - After TASK_CONTENTOPS_0099

LOCAL ONLY | NO NETWORK | NO PROVIDER | NO PLATFORM | NO CREDENTIALS | NO POSTING

Short operational guide for a local IDE/CLI worker. Run from the repo or use
`git -C` with the absolute repo path.

## Repo path
A:\Capital Chronicle\tools\cc-live-contentops

## First commands (orient)
- git -C "A:\Capital Chronicle\tools\cc-live-contentops" status --short
- git -C "A:\Capital Chronicle\tools\cc-live-contentops" log --oneline --decorate -10
- python -m live_contentops.cli status

## Pre-alpha pipeline summaries (read-only)
- python -m live_contentops.cli pre-alpha-content-engine-summary
- python -m live_contentops.cli pre-alpha-prompt-pack-summary
- python -m live_contentops.cli pre-alpha-draft-renderer-summary
- python -m live_contentops.cli pre-alpha-manual-review-summary
- python -m live_contentops.cli pre-alpha-manual-export-summary

## State / context summaries (read-only)
- python -m live_contentops.cli alpha-wait-state-summary
- python -m live_contentops.cli ide-cli-document-bundle-summary

## Test commands
- python -m pytest -q
- python -m pytest -q tests/test_pre_alpha_content_engine.py tests/test_pre_alpha_prompt_pack.py tests/test_pre_alpha_draft_renderer.py tests/test_pre_alpha_manual_review.py tests/test_pre_alpha_manual_export.py tests/test_security_scans.py

## Safe read-only inspection
- Read docs under docs/ (start with CURRENT_STATE_SUMMARY_AFTER_0099.md).
- Read live_contentops/*.py modules and schemas/pre_alpha_*.json.
- Use search/read tools rather than executing code that touches the network.

## Hard rules
- Use `git -C "A:\Capital Chronicle\tools\cc-live-contentops"` if your terminal
  starts in a sibling repo.
- Never run `git add .` - stage explicit paths only.
- Never edit, stage, or commit `.gitignore` (operator-owned drift).
- Never read env files or credentials.
- Never make network/provider/search/platform calls.
- Never reopen the Telegram lane (stopped by operator).
- Never modify the sibling cc-contentops repo or the Capital Chronicle core repo.

## Closing a task
Use the evidence packet template in
docs/IDE_CLI_EVIDENCE_PACKET_TEMPLATE_AFTER_0074.md.

## Next recommended task
TASK_CONTENTOPS_0101_PRE_ALPHA_END_TO_END_LOCAL_DEMO_PACKET_FROM_SEED_TO_LEDGER_V0
