# TASK_CONTENTOPS_0149 — Dry-Run Publish Batch Manifest (V0)

## Objective
Build a local-only, dry-run-only Publish Batch Manifest for future approved-only
multi-platform publishing. This defines the batch object that will eventually
support a one-button publish-all workflow, but it enables no live publishing,
platform APIs, credentials, OAuth, scheduling, backend/server behavior, provider
calls, or public-ready final approval. It models publish batch metadata, target
platform selection, per-platform payload previews, draft/review source lineage,
manual approval gate requirements, kill switch requirement, idempotency planning,
redacted audit log planning, partial failure planning, dry-run validation status,
and why live publish and one-button publish-all are NOT ENABLED.

This is a dry-run manifest task only. It is explicitly:
- NOT a live platform integration task
- NOT a credential/API-key/OAuth setup task
- NOT a posting/scheduling task
- NOT a backend/server task
- NOT a provider/LLM API task
- NOT a web/search/news/RSS/scraping task
- NOT a public-ready approval task

## Allowed Scope (built in this task)
- `schemas/dry_run_publish_batch_manifest_packet.schema.json`
- `live_contentops/dry_run_publish_batch_manifest.py` — validator + `summary()`.
- `fixtures/dry_run_publish_batch_manifest/` — valid fixture + 19 negative fixtures.
- CLI command `pre-alpha-dry-run-publish-batch-manifest-summary`.
- Tests in `tests/test_dry_run_publish_batch_manifest.py`.
- This runbook.

## Forbidden Scope (NOT built, NOT enabled)
- Live platform adapter, platform API client, OAuth flow, API key/token setup.
- Credential loading or `.env` reads, backend/server.
- Publish button, one-click publish-all action, scheduler, live posting.
- Provider/LLM API calls, web/search/news/RSS fetch, scraping, market-data API.
- Newsletter sender/SMTP/CMS integration, autonomous replies/DMs.
- Public-ready final copy generation, public-ready approval system.

## Why This Is a Dry-Run Manifest Only
The packet sets `dry_run_only=true` and fails closed if false. The
`readiness_status` records `dry_run_validation_status=modeled_only` and
`live_adapter_not_yet_complete=true`. Every per-platform payload preview has
`platform_adapter_status=not_implemented`, `dry_run_preview_only=true`, and
`live_execution_status=disabled`. No payload is a `final_payload`; preview text is
`placeholder_or_review_summary_only`.

## Why One-Button Publish-All Remains Disabled
`publish_all_button_enabled_now`, `one_button_publish_all_enabled_now`, and
`publish_approval_system_created` are all false and fail closed if true. The
`readiness_status.one_button_publish_all_not_enabled` stays true. The manifest
describes the future handoff but executes none of it.

## Why No Platform API Keys/Tokens Are Needed Now
This is dry-run batch manifest modeling only. The packet sets
`credentials_requested_now`/`credential_read_allowed_now`/
`credential_operator_action_required_now` false and
`credential_operator_action_required_later` true. Each payload preview marks
`credentials_requested_now`/`credential_read_allowed_now` false. No keys, tokens,
app secrets, OAuth, bot/page/refresh tokens, or account credentials are requested.

## What Future Tasks Will Require Operator API/Key/Token Setup
The `future_live_handoff` references requires_credential_and_secret_policy,
requires_one_platform_live_pilot_gate, and requires_approved_only_publish_all_gate.
Operator API keys/tokens will be requested only at those later, explicitly
approved credential/live-adapter stages — never in 0149.

## Relationship to 0148 Platform Capability Registry
Target platform selection is constrained to the 0148 registry set (telegram,
linkedin, x, threads, substack_or_newsletter, manual_external_posting). Any
target outside that set fails closed (`unsupported_platform_target`). The manifest
links the readiness packet and registry by id reference only.

## Target Platform Selection Model
`target_platform_ids` lists chosen registry platforms; the valid fixture selects
telegram, linkedin, and manual_external_posting. Each must have a matching
per-platform payload preview.

## Per-Platform Payload Preview Model
Each preview carries `platform_adapter_status=not_implemented`,
`dry_run_preview_only=true`, `live_execution_status=disabled`, all credential and
live flags false, visible source refs/limitations/content type, manual review
required, not public-postable, `publish_ready=false`, `final_payload=false`, and
`payload_text_preview_status=placeholder_or_review_summary_only`. Previews are
review summaries/placeholders, never final ready-to-post social copy.

## Source Lineage and Limitation Requirements
`source_lineage_policy` requires linked review chain; `limitation_visibility_policy`
requires limitations and forbids hiding missing/degraded data. Each preview must
keep `source_refs_visible` and `limitations_visible` true or validation fails.

## Kill Switch Requirement
`kill_switch_required=true` (fail closed if false). The `kill_switch_model` blocks
live execution when active and defaults `current_live_execution_status=disabled`.

## Redacted Audit Log Requirement
`redacted_audit_log_required=true` (fail closed if false). The
`redacted_audit_log_policy` requires secrets never logged, platform response
logging future-only, and credentials redacted later.

## Idempotency and Partial Failure Planning
`idempotency_policy_required` and `partial_failure_policy_required` are true and
fail closed if false. The policies mark idempotency keys, duplicate-publish
prevention, per-platform result tracking, and retry as future-only with no live
generation/retry now.

## Manual Approval Gates
`manual_approval_gate_required=true`. The `manual_approval_gate_model` requires
operator review, dry-run validation, source refs, limitations, and safety
validation, while keeping `public_ready_approval_allowed_now`,
`live_approval_allowed_now`, and `approved_for_live_publish` false.

## Safety / North Star Guarantees
- No backend/server. No repo web search/scraping/news API/market-data API.
- No provider/LLM API calls. No platform API/live posting/scheduler.
- No newsletter/CMS/email provider action. No public-ready content generation.
- No credential/env reads.
- The safety policy blocks buy/sell/hold, long/short, target price, position
  sizing, entry/exit, model-prediction/signal language, alpha/artifact claims
  without real approval, fake performance claims, unsupported numeric claims,
  public-ready final copy, live publish approval, and one-button publish-all.
- This supports future approved-only publish automation by defining the batch
  object, gates, and policies that must pass first. It amplifies macro thesis QA,
  data sufficiency, forecast readiness, and failure forensics, and never frames
  Capital Chronicle as a Bloomberg replacement, AI trading bot, signal service,
  execution system, or guaranteed prediction engine.

## Capability Statement
No live posting, platform API, credential/env read, API key/OAuth, scheduler,
scraping, web search, news/RSS/market-data API, newsletter sending, CMS/email-
provider integration, LLM provider call, backend server, live adapter, publish
button, one-button publish-all, publish approval, or public-ready copy capability
was added by this task. The layer is a local, dry-run-only, fail-closed publish
batch manifest model.

