# Approval Ledger, Kill Switch, and Redacted Audit - After TASK_CONTENTOPS_0079

LOCAL ONLY | ADVISORY ONLY | AUTHORITY READINESS ONLY | NOT PUBLIC POSTABLE
NO LIVE POSTING | NO MOCK PUBLISH FLOW (that is 0080) | NO PLATFORM API
NO CREDENTIALS | NO NETWORK | NO SCHEDULING | NO REPLIES/DMS | NO SCRAPING
HUMAN (OPERATOR) APPROVAL REQUIRED

This is the local authority layer that later tasks must pass before any mock
(0080) or live (future) publishing path can proceed. It never posts, never
implements a transport, never reads credentials, and never enables live posting.
Audit events are evidence only, not authority to post.

## Components
- `schemas/approval_ledger_record.schema.json` - approval ledger record contract.
- `schemas/publish_kill_switch_state.schema.json` - publish kill-switch contract
  (distinct name to avoid clobbering the legacy `kill_switch_state.schema.json`).
- `schemas/redacted_audit_event.schema.json` - redacted audit event contract.
- `live_contentops/approval_audit_contracts.py` - validators, ledger helpers,
  proceed-checks, redaction, and summary.
- `fixtures/approval_audit/*.json` - valid + invalid fixtures.

## Approval states
`draft_review_only`, `platform_dry_run_ready`, `operator_review_required`,
`operator_approved_for_mock_publish`, `operator_approved_for_live_publish_later`,
`blocked`, `revoked`.

Semantics:
- No state enables live posting now. `live_posting_enabled` is always false.
- `operator_approved_for_live_publish_later` is future-intent only; the live API
  remains disabled and `can_proceed_to_live_publish_later(...)` always returns
  allowed=false in this task.
- `blocked` and `revoked` fail closed for every downstream publish path.

## Kill switch
`default_kill_switch_state()` returns the safe default: `enabled=false`,
`blocks_mock_publish=true`, `blocks_live_publish=true`, `fail_closed=true`.
Validation rejects any state that sets `blocks_live_publish=false` or
`fail_closed=false`.

## Proceed checks (fail closed)
- `can_proceed_to_mock_publish(approval, kill_switch)` -> allowed only when the
  approval record is valid AND in state `operator_approved_for_mock_publish` AND
  the kill switch sets `blocks_mock_publish=false`. Missing/invalid/blocked/
  revoked approvals and a default (blocking) kill switch all fail closed.
- `can_proceed_to_live_publish_later(...)` -> always allowed=false.

## Redacted audit events
`build_redacted_audit_event(...)` redacts secret-like substrings (bearer tokens,
api/secret/client keys, passwords, bot tokens, `sk-...`, PEM private keys) before
they are ever stored, replacing them with `[REDACTED]`. `validate_audit_event`
fails closed if a persisted redacted payload still contains a secret-like string
or if any safety flag (`contains_secret`, `raw_secret_detected`,
`credential_accessed`, `network_accessed`, `live_posting_enabled`) is wrong.
Detection patterns operate on synthetic test strings only; no real secret is
read, logged, or persisted.

## Ledger storage
`append_approval_record(path, record)` appends a validated record to a
caller-supplied local JSONL path (append-only). Tests use `tmp_path`; this module
creates no committed runtime ledger and performs no network access.

## Boundary restatement
Authority contracts only. No live posting, no mock publish flow (deferred to
0080), no platform/provider API clients, no credentials, no network, no
scheduling, no replies/DMs, no scraping. Artifact-backed Capital Chronicle
content remains blocked until real approved alpha artifacts exist.
