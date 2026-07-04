# TASK_CONTENTOPS_0151 — Redacted Publish Audit Log and Secret Evidence Guard (V0)

## Objective
Build a local-only Redacted Publish Audit Log and Secret Evidence Guard for future
publish adapters. This is the audit/evidence safety layer that must exist before any
live platform adapter, credential setup gate, or one-platform live pilot. It models
redacted publish audit log packets, dry-run publish batch audit linkage, secret-safe
evidence packet requirements, credential event redaction, future-only platform
response redaction, kill-switch audit fields, a no-secret scan result model, an audit
event taxonomy, forbidden evidence content, and fail-closed validation for any
secret-like value or live-action claim.

This is an audit/evidence guard task only. It is explicitly:
- NOT a credential collection / API-key / OAuth / credential validation task
- NOT a live platform adapter / posting / scheduling task
- NOT a backend/server / provider-LLM / web/search/news/RSS/scraping task
- NOT a public-ready approval task

## No Platform API/Key/Token Needed From Operator Now
- platform API/key/token needed from operator now: no
- platform API/key/token needed from operator later: yes, only in a later explicitly
  approved live-adapter or credential-setup gate

Credential setup remains FUTURE_ONLY, NOT_REQUESTED_NOW, NOT_READ_NOW,
NOT_VALIDATED_NOW, NEVER_COMMIT_SECRETS.

## Allowed Scope (built in this task)
- `schemas/redacted_publish_audit_log_packet.schema.json`
- `live_contentops/redacted_publish_audit_log.py` — validator, secret-value
  detector with detector-source false-positive handling, and `summary()`.
- `fixtures/redacted_publish_audit_log/` — valid fixture + 17 negative fixtures.
- CLI command `pre-alpha-redacted-publish-audit-log-summary`.
- Tests in `tests/test_redacted_publish_audit_log.py`.
- This runbook.

## Forbidden Scope (NOT built, NOT enabled)
- Live platform adapter, platform API client, OAuth flow, API key/token setup.
- Credential loading, `.env` reads, OS environment reads, credential validation.
- Backend/server, publish button, one-click publish-all, scheduler, live posting.
- Provider/LLM API calls, web/search/news/RSS fetch, scraping, market-data API.
- Newsletter sender/SMTP/CMS integration, autonomous replies/DMs.
- Public-ready final copy generation, public-ready approval system.

## Redacted Publish Audit Log Model
The packet uses `audit_mode=redacted_audit_and_secret_evidence_guard_only` with
`audit_log_model_only=true` and `evidence_guard_model_only=true`. Audit events carry
event_id, event_type, linked_packet_id, redaction_status, secret_values_present,
credential_values_present, platform_response_values_present, evidence_safe,
kill_switch_status, live_action_performed, platform_api_called, created_at, notes.
Allowed event types cover dry-run manifest creation, payload preview validation,
manual review gate checks, kill-switch checks, credential-policy-no-values checks,
no-secret scan completion, redaction policy checks, blocked live-action detection,
future platform response redaction planning, and evidence export checks. Forbidden
event types (live_post_succeeded/failed, platform_api_called, credential_value_read/
validated, oauth_flow_completed, token_refreshed, publish_all_executed,
scheduled_post_created) fail closed.

## Secret-Safe Evidence Packet Rules
`evidence_packet_policy` allows slot names only, redaction status only, and
no-secret scan results only. It forbids secret values and partial token values, and
sets `allow_env_contents`, `allow_os_env_values`, `allow_token_snippets`,
`allow_screenshots_with_secrets`, `allow_logs_with_secrets`,
`allow_oauth_callback_values`, and `allow_platform_response_bodies_with_credentials`
all false. Any of these being true fails closed.

## No-Secret Scan Result Model
`no_secret_scan_result_model` records scan_id, scanned_scope_label,
scan_command_label, scan_result_status, real_secret_patterns_found,
secret_like_value_detected_count, false_positive_notes, detector_patterns_redacted,
evidence_safe, and created_at. The validator's secret detector scans the whole
packet for private keys, AWS/GitHub/Slack/Telegram tokens, bearer tokens, Google
OAuth tokens, and JWTs.

## Detector Regex False-Positive Handling
Detector-source keys (false_positive_notes, scan_command_label,
detector_patterns_redacted, detector_pattern_examples) are exempt from secret
detection so the scan model can describe its own regex patterns without tripping
itself. Real or realistic token-like values anywhere else still fail closed.

## Credential Event Redaction Policy
`credential_event_redaction_policy` requires credential events redacted, forbids
credential_values_present, and permits slot names only. Any audit event with
`secret_values_present=true` or `credential_values_present=true` fails closed.

## Future Platform Response Redaction Policy
`platform_response_redaction_policy_future_only` keeps platform response logging
future-only, requires later redaction, opt-in only, with no response bodies logged
now. An audit event may set `platform_response_values_present=true` only when its
`redaction_status=redacted_future_only`; otherwise it fails closed.

## Kill-Switch Audit Model
`kill_switch_audit_model` requires kill_switch_audit_required, kill_switch_status_
checked, kill_switch_halt_active, live_execution_blocked_when_active, and
`current_live_execution_status=disabled`. Missing the model or setting
`kill_switch_audit_required=false` fails closed.

## No Real Secrets / No Reads
No real secrets are placed in the repo, fixtures, docs, or tests. The packet keeps
`env_read_allowed_now`, `os_env_read_allowed_now`, and
`credential_validation_enabled_now` false. The repo reads no `.env`, no OS
environment values, and runs no credential validation. No secret values or token
snippets and no screenshots/logs containing secrets are permitted in evidence.

## Relationship to 0149 and 0150
The packet links the 0149 dry-run publish batch manifest and the 0150 credential and
secret policy by id reference. It supplies the redacted audit log and secret evidence
guard that the readiness future_task_sequence requires before any one-platform live
pilot or approved-only publish-all gate.

## Safety / North Star Guarantees
- No backend/server. No repo web search/scraping/news API/market-data API.
- No provider/LLM API calls. No platform API/live posting/scheduler.
- No newsletter/CMS/email provider action. No public-ready content generation.
- No credential/env reads. No OAuth flow. No credential validation.
- The safety policy blocks buy/sell/hold, long/short, target price, position sizing,
  model-prediction/signal language, alpha/artifact claims without real approval, and
  Bloomberg-replacement/AI-trading-bot/signal-service framing.
- This supports future approved-only publish automation by guaranteeing audit and
  secret-evidence safety before any live capability exists. It amplifies macro thesis
  QA, data sufficiency, forecast readiness, and failure forensics.

## Capability Statement
No live posting, platform API, credential/env read, OS-env read, API key/OAuth,
credential validation, scheduler, scraping, web search, news/RSS/market-data API,
newsletter sending, CMS/email-provider integration, LLM provider call, backend
server, live adapter, publish button, one-button publish-all, publish approval, or
public-ready copy capability was added by this task. The layer is a local,
fail-closed redacted audit log and secret evidence guard model holding no real
secrets.

