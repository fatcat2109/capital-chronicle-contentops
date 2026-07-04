# TASK_CONTENTOPS_0079_LOCAL_APPROVAL_LEDGER_KILL_SWITCH_AND_AUDIT_CONTRACT_V0

## Task scope
Build the local authority layer for future supervised publishing readiness:
approval ledger contract, publish kill-switch contract, and redacted audit event
contract. Readiness only: no live posting, no mock publish flow (that is 0080),
no platform API clients, no credential reads, no scheduling, no scraping, no
replies/DMs, no public-ready content.

## Files created/changed
- Created: schemas/approval_ledger_record.schema.json
- Created: schemas/publish_kill_switch_state.schema.json (distinct from the
  pre-existing tracked schemas/kill_switch_state.schema.json, which was left
  untouched)
- Created: schemas/redacted_audit_event.schema.json
- Created: live_contentops/approval_audit_contracts.py
- Created: fixtures/approval_audit/valid_approval_for_mock_publish.json
- Created: fixtures/approval_audit/valid_kill_switch_disabled_blocks.json
- Created: fixtures/approval_audit/valid_redacted_audit_event.json
- Created: fixtures/approval_audit/invalid_missing_approval.json
- Created: fixtures/approval_audit/invalid_revoked_approval.json
- Created: fixtures/approval_audit/invalid_secret_in_audit_event.json
- Created: tests/test_approval_audit_contracts.py
- Created: docs/APPROVAL_LEDGER_KILL_SWITCH_AND_AUDIT_AFTER_0079.md
- Created: docs/TASK_CONTENTOPS_0079_LOCAL_APPROVAL_LEDGER_KILL_SWITCH_AND_AUDIT_CONTRACT_V0.md (this report)

## What it does
- Approval ledger: 7 approval states; deterministic validator; append-only JSONL
  helper that requires a caller-supplied local path (tests use tmp_path).
- Kill switch: safe default (disabled + blocks mock + blocks live + fail_closed);
  validator forbids unblocking live or disabling fail_closed.
- Proceed checks: can_proceed_to_mock_publish fails closed unless approval is
  operator_approved_for_mock_publish and the switch permits mock;
  can_proceed_to_live_publish_later always returns allowed=false.
- Redacted audit events: builder redacts secret-like strings before storage;
  validator fails closed on any unredacted secret-like string or wrong flag.

## Design note
The schema name publish_kill_switch_state.schema.json was chosen because a
legacy tracked schemas/kill_switch_state.schema.json (generic shape, used by the
older live_contentops/kill_switch module) already exists. The legacy file was
NOT modified, to avoid weakening or colliding with existing behavior.

## What remains disabled
Live posting; mock publish flow (0080); platform/provider/LLM/search API clients;
credentials/env reads; network; scheduling; autonomous replies/DMs; scraping;
content generator; public-postable/publish-ready content; real alpha artifact
access; Capital Chronicle core repo reads/writes.

## Validation run
- python -m pytest -q: 426 passed (was 408; +18 new).
- python -m pytest -q tests/test_approval_audit_contracts.py: 18 passed.
- alpha-wait-state-summary: WAITING_FOR_REAL_CAPITAL_CHRONICLE_ALPHA_ARTIFACTS;
  public_content_allowed_now=false (wait-state preserved).
- git diff --check: clean.
- Suspicious scan over changed files: no functional network/credential/
  scheduler/SDK matches. Secret-like patterns appear only as redaction-detection
  regexes and synthetic test/fixture strings (BENIGN_GUARDRAIL_TEXT).

## Next task
TASK_CONTENTOPS_0080_LOCAL_MOCK_ADAPTER_PUBLISH_FLOW_AND_METRICS_CAPTURE_DRY_RUN_V0
