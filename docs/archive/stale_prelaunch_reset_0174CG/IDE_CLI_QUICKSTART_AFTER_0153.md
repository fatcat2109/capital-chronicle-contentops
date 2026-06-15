# IDE / Cline CLI Quickstart (After 0153)

## Repo
- Path: A:\Capital Chronicle\tools\cc-live-contentops
- Branch: master
- Baseline HEAD: a644f82 (accepted through 0153)

## Safe Validation Commands
- python -m pytest -q
- python -m pytest -q tests/test_telegram_credential_setup_operator_guide.py
- git status --short
- git diff --check

## Useful CLI Summary Commands
- python -m live_contentops.cli status
- python -m live_contentops.cli operator-command-summary
- python -m live_contentops.cli pre-alpha-telegram-credential-setup-guide-summary
- python -m live_contentops.cli pre-alpha-telegram-live-pilot-gate-summary
- python -m live_contentops.cli pre-alpha-redacted-publish-audit-log-summary
- python -m live_contentops.cli pre-alpha-publish-adapter-credential-secret-policy-summary
- python -m live_contentops.cli pre-alpha-dry-run-publish-batch-manifest-summary
- python -m live_contentops.cli pre-alpha-publish-automation-readiness-summary
- python -m live_contentops.cli pre-alpha-daily-content-studio-run-summary

## Forbidden Commands / Actions
- Do not read .env or the operator env file.
- Do not read OS environment variable values.
- Do not call Telegram or any platform/provider/news API.
- Do not run posting, scheduling, scraping, or live adapters.
- Do not use git add . ; stage explicit files only.
- Do not run git clean / reset --hard / restore / checkout for cleanup.

## How To Run The Next Cline Prompt
1. Open a fresh Cline CLI session in the repo root.
2. Confirm HEAD is the latest accepted commit on master.
3. Paste the next task prompt
   (TASK_CONTENTOPS_0155_TELEGRAM_REDACTED_CREDENTIAL_PRESENCE_CHECK_LOCAL_ONLY_V0).
4. Let Cline run preflight, implement, validate, and produce a FINAL EVIDENCE PACKET.

## Reminder
Do not read the operator env file until an explicitly scoped presence-check task
(0155) authorizes reading only an approved local env source for boolean/redacted
evidence — never values, never a Telegram API call.
