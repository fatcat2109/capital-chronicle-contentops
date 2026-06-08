# IDE/CLI Allowed Maintenance Tasks - After TASK_CONTENTOPS_0074

LOCAL ONLY | ADVISORY ONLY | NO RUNTIME CAPABILITY

While the repo is in the terminal alpha wait-state, only local-maintenance work
is allowed unless the operator selects something else or real Capital Chronicle
alpha artifacts arrive.

## Allowed maintenance categories
- Docs refresh (clarify, update, correct existing docs).
- Bundle/path proof (verify exact committed doc paths; avoid stale naming).
- Test-only guardrail hardening (add negative tests; never weaken guardrails).
- Typo / README correction.
- Evidence addendum (close evidence gaps without new runtime behavior).
- Final bundle refresh (regenerate safe Project Sources bundle docs).
- Stale Project Sources cleanup guidance (document what to remove before upload).

## Forbidden maintenance categories
- New synthetic content generation.
- Live posting / platform API.
- Provider / search integration.
- Credential / env reads.
- Capital Chronicle core repo reads/writes.
- Public-post-ready fixture content.
- Auto-approval / scheduling.
- Trading / signal / execution / broker language.

## Rules for every maintenance task
- One focused commit, explicit paths, never `git add .`.
- Never touch operator-owned `.gitignore`.
- Preserve the terminal wait-state pointer in live_contentops/status.py.
- Run the full test suite and a suspicious scan before committing.
- Close with the evidence packet template
  (docs/IDE_CLI_EVIDENCE_PACKET_TEMPLATE_AFTER_0074.md).
