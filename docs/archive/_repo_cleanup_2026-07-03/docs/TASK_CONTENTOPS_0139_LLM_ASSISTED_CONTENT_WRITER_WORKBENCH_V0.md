# TASK_CONTENTOPS_0139 — LLM-Assisted Content Writer Workbench (V0)

## Objective
Build a local-only deterministic control layer around externally written drafts
and externally used LLM prompt packs. The workbench describes how drafts are
classified, source-gated, platform-fit-noted, and routed through manual review —
without the repo ever calling an LLM/provider, generating final public-ready
posts, or auto-approving copy.

This is explicitly:
- NOT a provider/LLM API task (repo never calls OpenAI/Claude/Gemini/etc.)
- NOT a prompt execution engine
- NOT a final public-ready post generator
- NOT a posting / scheduling / scraping / newsletter / CMS task

## Allowed Scope (built in this task)
- `schemas/llm_content_writer_workbench_packet.schema.json` — packet schema.
- `live_contentops/llm_content_writer_workbench.py` — deterministic validator and
  `summary()`.
- `fixtures/llm_content_writer_workbench/` — one valid fixture and six negative
  fixtures.
- CLI command `pre-alpha-llm-content-writer-workbench-summary`.
- Tests in `tests/test_llm_content_writer_workbench.py`.
- This runbook.

## Forbidden Scope (NOT built, NOT enabled)
- Repo-side OpenAI/Claude/Gemini/provider API calls or prompt execution.
- Live web/news/market-data search or API integration.
- Scraping.
- Platform API clients, credential loading, or `.env` reads.
- Scheduler / auto-posting / autonomous replies or DMs.
- Newsletter sender / SMTP / CMS integration.
- Public-ready or fake content generation.

## Prompt Pack / Template-Only Model
Prompt pack templates are descriptive scaffolding for an operator to use with an
external LLM. Each template hard-asserts:
- `template_only = true`
- `external_llm_use_only = true`
- `provider_call_allowed_by_repo = false`
- `repo_executes_prompt = false`
- `manual_review_required = true`
- `not_public_postable = true`
- `public_ready_allowed_now = false`

The repo stores and validates templates only. It never sends them to a provider
and never executes them.

## External LLM Use Boundary
The boundary is strict: any drafting done by an LLM happens outside the repo, by
the operator. Drafts re-enter as external input described by
`draft_input_contract` (`repo_generates_draft = false`). The repo's role is
classification, source-gating, safety review, and manual-review routing.

## Repo Does Not Call Providers / Does Not Generate Final Posts
`summary()` keeps every provider/live/external counter at zero or false:
`provider_call_enabled_count`, `repo_prompt_execution_enabled_count`,
`public_ready_allowed_count`, `publish_ready_count`, `auto_approval_enabled_count`,
`platform_export_final_enabled_count`, `newsletter_send_enabled_count`,
`cms_integration_enabled_count`, plus `provider_call_used_by_repo`,
`search_call_used_by_repo`, `network_call_used_by_repo`,
`platform_action_used_by_repo`, `credential_or_env_read_used`,
`scheduler_accessed`, `scraping_allowed_now`, `autonomous_reply_dm_enabled`.

## Manual Review Requirement
The output policy fails closed unless `manual_review_required = true` and
`not_public_postable = true`, with `publish_ready`, `auto_approval_allowed`,
`public_ready_allowed_now`, `platform_export_final_allowed_now`,
`newsletter_send_enabled_now`, and `cms_integration_enabled_now` all false. The
review policy must require manual review and forbid auto-approval.

## Claim Classification & Safety
Claim classifications include `first_party_product_process`,
`evergreen_macro_education`, `cited_factual_claim`,
`current_factual_claim_requires_source`, `market_sensitive_claim_review_only`,
`unsupported_numeric_claim_blocked`, `signal_or_trade_claim_blocked`, and
`artifact_backed_claim_blocked_until_real_artifact`.

The validator blocks trading/signal/execution language (buy/sell/hold,
long/short, target price, position sizing, entries/exits, broker, order routing,
execution, signal, "our model predicts", "our signal says", guaranteed
prediction), AI-trading-bot / Bloomberg-replacement / signal-service framing,
fake-alpha/performance and unsupported-numeric claims, and "Capital Chronicle
alpha says" before real approved artifacts. Source-required claims must keep
`source_references_required = true`.

## Relationship to 0138 Social Platform Foundation
`social_platform_foundation_linkage` and `platform_fit_policy` reference the
0138 Social Platform Foundation control plane. Platform-fit here is notes-only;
final platform export remains disabled, consistent with 0138's per-platform
`not_public_postable` / `manual_review_required` guarantees.

## How This Prepares the Grounded News Angle Workbench
`angle_taxonomy` and `future_handoff.grounded_news_angle_workbench_handoff_ready`
establish the structural seam for the later grounded news angle workbench: sourced
angles will flow into the same claim-classification and source-requirement policy,
with signal language blocked and manual review required, while
`no_capability_enabled_now` confirms nothing live is turned on.

## Capability Statement
No live posting, platform API, credential/env read, scheduler, scraping,
newsletter sending, CMS/email-provider integration, LLM provider call, or
autonomous reply/DM capability was added by this task. The layer is a local,
fixture-driven, fail-closed control-plane description only.
