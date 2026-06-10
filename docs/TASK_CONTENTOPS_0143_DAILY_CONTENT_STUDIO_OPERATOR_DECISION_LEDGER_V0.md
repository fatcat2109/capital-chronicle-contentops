# TASK_CONTENTOPS_0143 — Daily Content Studio Operator Decision Ledger (V0)

## Objective
Record Jim's manual review decisions on Daily Content Studio run packets (0141)
and Markdown review exports (0142) in a local-only, deterministic audit/control
layer. The ledger captures which run packet and Markdown export were reviewed,
Jim's manual decision state, the decision reason taxonomy, source/limitation
blockers, safety blockers, allowed manual-only next actions, explicit
not-public-postable status, and explicit no-live/no-provider/no-platform/
no-scheduler state.

This is explicitly:
- NOT a publish approval system
- NOT a live posting task
- NOT a scheduling task
- NOT a platform/API task
- NOT an LLM/provider API task
- NOT a web/news/search/scraping task
- NOT a newsletter/CMS/email provider task
- NOT a public-ready copy generator

## Allowed Scope (built in this task)
- `schemas/daily_content_studio_operator_decision_ledger_packet.schema.json`
- `live_contentops/daily_content_studio_operator_decision_ledger.py` — validator
  and `summary()`.
- `fixtures/daily_content_studio_decision_ledger/` — one valid fixture and ten
  negative fixtures.
- CLI command `pre-alpha-daily-content-studio-decision-ledger-summary`.
- Tests in `tests/test_daily_content_studio_operator_decision_ledger.py`.
- This runbook.

## Forbidden Scope (NOT built, NOT enabled)
- Live publish approval, public-ready approval, platform posting/API, scheduling.
- Provider/LLM API calls, web/search/news/RSS fetch, scraping, market-data API.
- Newsletter sender / SMTP / CMS integration.
- Credential loading or `.env` reads.
- Autonomous replies/DMs.
- Public-ready or final social copy generation.
- Real Capital Chronicle artifact-backed claims.

## How This Follows 0142 Markdown Review Export
The 0142 Markdown Review Export renders a run packet into a human-readable review
artifact. This 0143 ledger sits immediately downstream: after Jim reads the
Markdown review, he records a decision in the ledger. Each decision record links
back to the reviewed run packet id (`reviewed_run_packet_id`) and the Markdown
export id (`reviewed_markdown_export_id`), creating a local audit trail of manual
review decisions.

## Manual Decision States and Reason Taxonomy
Allowed decision states: pending_review,
approved_for_manual_external_llm_prompting,
approved_for_manual_rewrite_outside_repo, needs_revision,
needs_source_or_limitation_fix, held_for_operator_review, rejected_by_operator,
blocked_by_safety_policy, archived_no_public_action.

Forbidden decision states (fail closed): approved_for_live_publish,
approved_for_auto_publish, approved_for_platform_api, approved_for_scheduler,
approved_for_provider_call, approved_for_newsletter_send,
approved_public_ready_final, approved_as_trading_signal.

Decision reason taxonomy: source_context_sufficient_for_review,
source_context_missing, limitation_note_missing, claim_risk_too_high,
signal_language_detected, unsupported_numeric_claim,
artifact_claim_without_real_artifact, platform_fit_needs_revision,
prompt_template_needs_revision, safe_for_manual_external_drafting_only,
safe_for_manual_rewrite_only, no_public_action.

Allowed manual next actions are review/external-only (review source context,
choose or reject angle card, copy prompt template for external LLM, manually
rewrite draft outside repo, revise source/limitation notes, rerun local
validation, manually record public URL later if Jim independently posts outside
repo). Forbidden next actions (auto_publish, schedule_post, live_publish,
send_newsletter, call_platform_api, call_provider_api, scrape_metrics,
fetch_market_data, auto_reply_or_dm, mark_public_ready_final,
convert_to_trading_signal) fail closed if presented as allowed.

## Why This Is Not a Publish Approval System
The ledger records manual operator review decisions only. The validator fails
closed if any decision record or packet policy grants live publish, public-ready,
platform API, provider call, scheduler, newsletter/CMS approval, auto approval,
publish-ready, or final social copy. There is no state that authorizes any live
or external action. A "decision" here is a review note, not an execution grant.

## No Repo Web Search / Scraping / News API / Market-Data API
The module reads local fixtures only and performs zero network or fetch
operations. `summary()` keeps every related counter at zero/false.

## No Provider/LLM API Calls
The repo never calls a provider; provider-call approval is a forbidden grant.

## No Platform API / Live Posting / Scheduler
Platform API, live posting, and scheduler approvals all fail closed.

## No Newsletter/CMS/Email Provider Action
Newsletter/CMS send approval fails closed; no provider is contacted.

## No Public-Ready Content Generation
The ledger records decisions, not content. `final_social_copy_generated` must be
false at packet and record level.

## No Credential/Env Reads
The module reads only local fixtures; it does not read `.env`, credentials, or
secrets. `credential_read_allowed_now` must be false.

## How This Supports Macro Thesis QA and the North Star
By forcing source-lineage and limitation confirmation, fail-closed safety checks,
and an explicit manual review trail, the ledger amplifies macro thesis QA, data
sufficiency, forecast readiness, and failure forensics. It never frames Capital
Chronicle as a Bloomberg replacement, AI trading bot, signal service, execution
system, or guaranteed prediction engine.

## Capability Statement
No live posting, platform API, credential/env read, scheduler, scraping, web
search, news/RSS/market-data API, newsletter sending, CMS/email-provider
integration, LLM provider call, autonomous reply/DM, publish approval, or
public-ready copy capability was added by this task. The layer is a local,
fixture-driven, fail-closed manual decision ledger only.
