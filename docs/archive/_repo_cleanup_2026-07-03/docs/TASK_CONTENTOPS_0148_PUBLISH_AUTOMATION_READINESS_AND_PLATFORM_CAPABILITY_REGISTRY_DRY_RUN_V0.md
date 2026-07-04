# TASK_CONTENTOPS_0148 — Publish Automation Readiness and Platform Capability Registry (Dry-Run V0)

## Objective
Build a local-only, dry-run-only Publish Automation Readiness and Platform
Capability Registry. This starts the roadmap toward an eventual approved-only
"one-button publish-all" workflow, but it enables no live publishing,
credentials, platform APIs, OAuth, scheduling, provider calls, or public-ready
final approval. It models which platforms may be supported later, their
placeholder capability constraints, what credential/API setup will be needed
later (future-only, not requested now), dry-run payload checks, readiness gates,
why one-button publish-all is currently NOT ENABLED, and the future task
sequence that must complete before asking Jim for API keys/tokens.

This is a planning/contract/readiness task only. It is explicitly:
- NOT a live platform integration task
- NOT a credential/API-key/OAuth setup task
- NOT a posting/scheduling task
- NOT a backend/server task
- NOT a provider/LLM API task
- NOT a web/search/news/RSS/scraping task
- NOT a public-ready approval task

## Allowed Scope (built in this task)
- `schemas/platform_capability_registry_packet.schema.json`
- `schemas/publish_automation_readiness_packet.schema.json`
- `live_contentops/publish_automation_readiness.py` — two validators + `summary()`.
- `fixtures/publish_automation_readiness/` — valid registry + readiness fixtures
  and twelve negative fixtures.
- CLI command `pre-alpha-publish-automation-readiness-summary`.
- Tests in `tests/test_publish_automation_readiness.py`.
- This runbook.

## Forbidden Scope (NOT built, NOT enabled)
- Live platform adapter, platform API client, OAuth flow, API key/token setup.
- Credential loading or `.env` reads, backend/server.
- Publish button, one-click publish-all action, scheduler, live posting.
- Provider/LLM API calls, web/search/news/RSS fetch, scraping, market-data API.
- Newsletter sender/SMTP/CMS integration, autonomous replies/DMs.
- Public-ready final copy generation, public-ready approval system.

## Why This Starts but Does NOT Enable One-Button Publish-All
The packet models a `publish_batch_model` whose `live_execution_status` is
`disabled` and `dry_run_status` is `modeled_only`. Packet booleans
`publish_all_button_enabled_now`, `one_button_publish_all_enabled_now`, and
`publish_approval_system_created` are all false and fail closed if true. The
readiness gate `one_button_publish_all_not_enabled` stays true. The roadmap is
described in `future_task_sequence`, but none of it is executed here.

## Why No Platform API Keys/Tokens Are Needed Now
This is dry-run readiness modeling only. The registry marks every platform's
`credential_setup_status` as `future_only_not_requested`,
`credentials_requested_now`/`credential_read_allowed_now`/`credentials_available`
as false, and `operator_action_required_now` as false. The readiness packet sets
`operator_action_required_now_for_credentials` false and
`operator_action_required_later_for_credentials` true. No keys, tokens, app
secrets, OAuth, bot/page/refresh tokens, or account credentials are requested.

## What Future Tasks Will Require Operator API/Key/Token Setup
The `future_task_sequence` lists: dry_run_publish_manifest,
credential_and_secret_policy, redacted_audit_log, one_platform_live_pilot_gate,
first_platform_live_adapter, multi_platform_dry_run_orchestrator,
approved_only_publish_all_gate. Operator API keys/tokens will only be requested
at the credential_and_secret_policy / first_platform_live_adapter stages, in a
later explicitly approved credential/live-adapter task — never in 0148.

## Platform Capability Registry Model
Six placeholder targets (telegram, linkedin, x, threads, substack_or_newsletter,
manual_external_posting). Each entry uses conservative placeholder constraints,
`adapter_status=not_implemented`, `requires_future_official_docs_verification=true`,
and all live/credential flags false. No exact live API facts are claimed.

## Credential Requirement Future-Only Model
Each platform's `credential_requirement_future_only` records a
`credential_type_placeholder`, `storage_policy_future_only`,
`redaction_required=true`, `never_commit_secrets=true`, `env_read_allowed_now=false`,
`operator_action_required_now=false`, and `operator_action_required_later=true`.

## Dry-Run Publish Readiness Model
The `dry_run_payload_model` requires source references, limitations, content type,
platform target, and not-public-postable status to be visible, with no
signal/trading language, no unsupported numeric claims, no fake artifact-backed
claims, and no final public-ready copy.

## Kill Switch and Redacted Audit Log Requirements
`kill_switch_required` and `redacted_audit_log_required` must both be true and
fail closed if false. The `kill_switch_model` halts all future live action and
defaults to active. The `audit_log_policy` requires redacted logs and never logs
secrets (future-only).

## Idempotency, Partial Failure, and Manual Approval Gates
`idempotency_policy` and `partial_failure_policy` flag the guards required later.
The `manual_approval_gate_model` requires human operator approval before any
future live action and forbids auto-approval.

## Safety / North Star Guarantees
- No backend/server. No repo web search/scraping/news API/market-data API.
- No provider/LLM API calls. No platform API/live posting/scheduler.
- No newsletter/CMS/email provider action. No public-ready content generation.
- No credential/env reads.
- This supports future approved-only publish automation by defining the gates,
  registry, and credential policy that must pass first. It amplifies macro thesis
  QA, data sufficiency, forecast readiness, and failure forensics, and never
  frames Capital Chronicle as a Bloomberg replacement, AI trading bot, signal
  service, execution system, or guaranteed prediction engine.

## Capability Statement
No live posting, platform API, credential/env read, API key/OAuth, scheduler,
scraping, web search, news/RSS/market-data API, newsletter sending, CMS/email-
provider integration, LLM provider call, backend server, live adapter, publish
button, one-button publish-all, publish approval, or public-ready copy capability
was added by this task. The layer is a local, dry-run-only, fail-closed readiness
and capability registry model.

