# Draft Review Packet - After TASK_CONTENTOPS_0077

LOCAL ONLY | ADVISORY ONLY | REVIEW ONLY | NOT PUBLIC POSTABLE
NO PROVIDER CALL | NO SEARCH CALL | NO PLATFORM ACTION | NO CREDENTIALS | NO FETCH
NO GENERATOR | NO AUTO-APPROVAL | HUMAN (JIM) FINAL REVIEW REQUIRED

This document defines the local-only, review-only draft review packet contract
for pre-alpha general/process and grounded-news drafts written OUTSIDE the repo.

## What this is
- A deterministic JSON contract plus a local validator
  (`live_contentops/draft_review_packet.py`,
  `schemas/draft_review_packet.schema.json`).
- It reviews drafts that an operator, an LLM-assisted workflow, or ChatGPT/Deep
  Research produced OUTSIDE the repo and supplied manually.
- It checks safety, citation linkage, claim quality/risk, forbidden language,
  and produces a review verdict plus required operator actions.

## What this is NOT
- It is NOT a content generator. It never writes final public copy.
- It is NOT final public copy and is NOT platform export.
- It is NOT a posting or scheduling path.
- It is NOT a fetcher. The repo never calls web/search/provider/LLM/platform APIs
  and never reads credentials.
- It does NOT auto-approve. Jim must manually rewrite, approve, and post.

## Core principle
LLM assistance is allowed only OUTSIDE the repo, as manually supplied text and
context. The repo reviews safety/citation/claim quality only. News stays a hook,
not a signal. Output is review context for Jim, never publishable copy.

## Packet shape (summary)
Required top-level fields: `packet_id`, `lane` (must be
`pre_alpha_general_process`), `subtype`, `draft_origin`, `draft_text`,
`linked_research_brief`, `source_references_used`, `claim_reviews`,
`platform_fit`, `safety_review`, `verdict`, `allowed_output_use`.

`linked_research_brief` must carry a `brief_id` and `brief_validated=true` (the
brief is validated separately by the 0076 grounded research brief contract).

Each citation-required claim review (`cited_factual_claim` /
`current_factual_claim`) must have `has_citation=true` and `source_ids` that
resolve to a `source_id` declared in `source_references_used`.

`safety_review` must keep `public_postable`, `publish_ready`, `artifact_backed`,
`provider_call_used_by_repo`, `search_call_used_by_repo`,
`platform_action_used_by_repo` all false, and `review_only`,
`manual_review_required`, `jim_final_review_required`, `no_financial_advice`,
`no_signal_language`, `no_execution_language` all true.

`verdict.status` is one of `local_review_pass`, `local_review_warn`,
`local_review_block`. A `local_review_pass` cannot coexist with blocking issues.

`allowed_output_use` must include `local_review_only` and `not_public_postable`.

## Blocking rules (validator)
A packet is invalid if any of these hold:
- lane is not `pre_alpha_general_process`;
- `public_postable=true` or `publish_ready=true`;
- `review_only`, `manual_review_required`, or `jim_final_review_required` not true;
- `artifact_backed=true`;
- any repo provider/search/platform flag is true;
- `draft_text` contains market-action language (buy/sell/hold/long/short/entry/
  exit/target/position sizing/broker/order routing/execution/signal/model says);
- `draft_text` implies Capital Chronicle alpha output exists;
- a current/cited factual claim lacks a citation;
- a cited claim references a source not declared in `source_references_used`;
- `claim_type` is `forbidden_claim`;
- `risk_level` is `blocked`;
- `verdict.status` is `local_review_pass` while blocking issues exist.

## Fixtures
- `fixtures/draft_review_packets/valid_review_only_grounded_news_draft.json` (valid).
- `fixtures/draft_review_packets/invalid_publish_ready_true.json`.
- `fixtures/draft_review_packets/invalid_uncited_current_claim.json`.
- `fixtures/draft_review_packets/invalid_forbidden_signal_language.json`.
- `fixtures/draft_review_packets/invalid_artifact_backed_claim.json`.

## Boundary restatement
This task reviews drafts produced outside the repo. It adds no generator, no
external calls, and no public-ready output. Jim must manually rewrite, approve,
and post. Artifact-backed Capital Chronicle content remains blocked until real
approved alpha artifacts exist.
