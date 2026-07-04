# TASK_CONTENTOPS_0144 — Daily Content Studio External Draft Review Packet (V0)

## Objective
Let Jim paste externally generated draft text back into the repo for
deterministic local review after using the accepted Daily Content Studio
workflow. The packet links the external draft to the 0141 run packet, 0142
Markdown review export, 0143 operator decision ledger, source/news context, the
selected angle card, the external LLM prompt-template handoff, and platform-fit
notes. The validator reviews the pasted draft for claim classification, source
reference coverage, limitation/freshness visibility, angle alignment, platform
fit, unsafe trading/signal/execution language, fake artifact-backed claims,
unsupported numeric claims, public-ready leakage, and manual review status.

This is explicitly:
- NOT a repo-side LLM generator
- NOT a provider/LLM API task
- NOT a final public-ready copy generator
- NOT an auto-approval task
- NOT a platform export/posting task
- NOT a web/news/search/scraping task
- NOT a newsletter/CMS/email provider task

## Allowed Scope (built in this task)
- `schemas/daily_content_studio_external_draft_review_packet.schema.json`
- `live_contentops/daily_content_studio_external_draft_review.py` — validator and
  `summary()`.
- `fixtures/daily_content_studio_external_draft_review/` — one valid fixture and
  twelve negative fixtures.
- CLI command `pre-alpha-daily-content-studio-external-draft-review-summary`.
- Tests in `tests/test_daily_content_studio_external_draft_review.py`.
- This runbook.

## Forbidden Scope (NOT built, NOT enabled)
- Provider/LLM API calls, repo-side prompt execution.
- Final public-ready copy generation, auto-approval.
- Platform final export, live posting, scheduling, platform API clients.
- Web/search/news/RSS fetch, scraping, market-data API integration.
- Newsletter sender / SMTP / CMS integration.
- Credential loading or `.env` reads.
- Autonomous replies/DMs.
- Real Capital Chronicle artifact-backed claims.

## How This Follows 0141, 0142, and 0143
The pipeline is: 0141 composes the daily run packet -> 0142 renders it into a
human-readable Markdown review -> 0143 records Jim's manual review decision ->
0144 (this task) accepts the externally written draft back for deterministic
local review. Each external draft review packet carries
`linked_daily_content_studio_run_packet_id`,
`linked_markdown_review_export_id`, and
`linked_operator_decision_ledger_packet_id` so the full local audit chain is
preserved.

## How Jim Manually Pastes External LLM Drafts Into Local Review
Jim takes a prompt template from the workflow, runs it in an external LLM of his
choice (outside the repo), then pastes the resulting draft text into an external
draft review packet's `external_draft_input.draft_text`. He marks
`generated_outside_repo` and `operator_pasted` true, supplies the source context
ids and selected angle card ids, and runs local validation. The repo only reads
and reviews; it never produced the draft.

## Why This Is Not Repo-Side LLM Generation
The repo never calls a provider and never executes a prompt.
`repo_generated_draft`, `repo_executes_prompt`, `provider_call_allowed_by_repo`,
and `provider_llm_api_allowed_now` all fail closed if true. The draft must be
generated outside the repo and pasted by the operator.

## Why This Is Not Public-Ready Final Copy
`publish_ready`, `public_ready_allowed_now`, and `final_social_copy_generated`
must be false. The validator also fails closed if the draft text says "ready to
post" or if `review_result.represented_as_final_social_copy` is true. The review
produces a manual-revision verdict, not publishable copy.

## Source Reference and Limitation Requirements
For claims classified `cited_factual_claim` or
`current_factual_claim_requires_source`, a source reference must be present.
Every reviewed claim must carry a limitation note. Missing source references or
limitation notes fail closed. The external draft input must also carry
`source_references_visible` and `limitation_notes_visible` true.

## Claim Classification and Safety Checks
Supported classifications: first_party_product_process,
evergreen_macro_education, cited_factual_claim,
current_factual_claim_requires_source, market_sensitive_review_only,
unsupported_numeric_claim_blocked, signal_or_trade_claim_blocked,
artifact_backed_claim_blocked_until_real_artifact. The draft-text safety scan
fails closed on trading/signal/execution/model-prediction language (buy, sell,
hold, long, short, target price, position sizing, "our model predicts", "our
signal says", broker/order/execution framing, guaranteed prediction, AI trading
bot / Bloomberg replacement / signal-service framing), on unsupported numeric /
fake alpha claims, and on "Capital Chronicle alpha says" without real approved
artifacts.

## No Repo Web Search / Scraping / News API / Market-Data API
The module reads local fixtures only and performs zero network or fetch
operations. `summary()` keeps every related counter at zero/false.

## No Provider/LLM API Calls
The repo never calls a provider; provider-call/prompt-execution flags fail closed.

## No Platform API / Live Posting / Scheduler
Platform API, live posting, final export, and scheduler all fail closed.

## No Newsletter/CMS/Email Provider Action
Newsletter/CMS API flags fail closed; no provider is contacted.

## No Credential/Env Reads
The module reads only local fixtures; it does not read `.env`, credentials, or
secrets. `credential_read_allowed_now` must be false.

## How This Supports Macro Thesis QA and the North Star
By forcing source-reference and limitation coverage, claim classification, and
fail-closed safety checks on externally written drafts, this layer amplifies
macro thesis QA, data sufficiency, forecast readiness, and failure forensics. It
never frames Capital Chronicle as a Bloomberg replacement, AI trading bot, signal
service, execution system, or guaranteed prediction engine.

## Capability Statement
No live posting, platform API, credential/env read, scheduler, scraping, web
search, news/RSS/market-data API, newsletter sending, CMS/email-provider
integration, LLM provider call, repo-side prompt execution, autonomous reply/DM,
publish approval, or public-ready copy capability was added by this task. The
layer is a local, fixture-driven, fail-closed external draft review surface only.

