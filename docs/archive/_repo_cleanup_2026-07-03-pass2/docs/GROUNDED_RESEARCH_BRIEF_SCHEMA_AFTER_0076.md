# Grounded Research Brief Schema - After TASK_CONTENTOPS_0076

LOCAL ONLY | ADVISORY ONLY | OPERATOR-SUPPLIED CONTEXT ONLY | NOT PUBLIC POSTABLE
NO PROVIDER CALL | NO SEARCH CALL | NO PLATFORM ACTION | NO CREDENTIALS | NO FETCH

This document defines the local-only contract for operator-supplied grounded
research briefs used by the pre-alpha Grounded News / Research Context Lane
(see PRE_ALPHA_GENERAL_PROCESS_AND_GROUNDED_NEWS_MASTER_PLAN_AFTER_0075.md,
section 12).

## What this is
- A deterministic JSON contract plus a local validator
  (`live_contentops/grounded_research_brief.py`,
  `schemas/grounded_research_brief.schema.json`).
- It validates research briefs that an operator or ChatGPT/Deep Research prepares
  OUTSIDE the repo and supplies manually.

## What this is NOT
- It is NOT a fetcher. The repo never calls web/search/provider/LLM/platform APIs
  and never reads credentials.
- It is NOT a content generator. It does not produce final public copy.
- It is NOT a publishing path. Every brief stays not-public-postable and
  manual-review-required. Public posting remains a manual decision by Jim.
- It is NOT artifact-backed. Briefs cannot claim Capital Chronicle alpha output.
  Artifact-backed Capital Chronicle content remains BLOCKED until real approved
  alpha artifacts exist and route through the existing intake gate.

## Core principle
News is a hook, not a signal. A current event may anchor education, data
sufficiency, forecast readiness, failure forensics, or product philosophy. It may
never become a market call, recommendation, or implied trade.

## Brief shape (summary)
Top-level required fields: `brief_id`, `lane` (must be
`pre_alpha_general_process`), `subtype`, `title`, `operator_supplied` (true),
`source_collection_method`, `sources[]`, `claims[]`, `safety_review`,
`allowed_output_use`.

Allowed subtypes: `grounded_news_context`, `official_data_explainer`,
`policy_process_commentary`, `macro_education_from_news`,
`forecast_readiness_from_news`, `data_sufficiency_from_news`,
`failure_forensics_from_news`.

Each source requires: `source_id`, `title`, `url`, `publisher_or_author`, a
date (`publication_date` or `accessed_date`), `source_type`, `credibility_note`,
`freshness_note`, `limitation_note`.

Each claim requires: `claim_id`, `claim_text`, `claim_type`, `claim_risk`.
Claim types: `first_party_philosophy`, `evergreen_education`,
`cited_factual_claim`, `current_factual_claim`, `market_sensitive_context`,
`forbidden_claim`. Claim risk: `low`, `medium`, `high`, `blocked`. Factual and
current claims require `requires_citation=true`, `has_citation=true`, and
`source_ids` that resolve to a declared source.

`safety_review` must keep `public_postable`, `artifact_backed`, `publish_ready`,
`provider_call_used_by_repo`, `search_call_used_by_repo`,
`platform_action_used_by_repo` all false, and `manual_review_required`,
`no_financial_advice`, `no_signal_language`, `no_execution_language` all true.

`allowed_output_use` must include `not_public_postable` and at least one of
`research_context_only` / `local_review_only`.

## Blocking rules (validator)
A brief is rejected if any of these hold:
- lane is not `pre_alpha_general_process`;
- `public_postable=true` or `publish_ready=true`;
- any repo provider/search/platform flag is true;
- a source is missing a URL or a date for factual/current claims;
- `claim_type` is `forbidden_claim`;
- `claim_risk` is `blocked`;
- claim text contains market-action language (buy/sell/hold/long/short/entry/
  exit/target/position sizing/broker/order routing/execution/signal/model says);
- claim implies Capital Chronicle alpha output exists (e.g. "Capital Chronicle
  alpha says", `artifact_id`, `dqr_status`, "our model predicts");
- a citation-required claim lacks a citation or references an unknown source.

## Fixtures
- `fixtures/grounded_research_briefs/valid_minimal_grounded_news_context.json`
  (valid).
- `fixtures/grounded_research_briefs/invalid_missing_source_url.json`.
- `fixtures/grounded_research_briefs/invalid_market_signal_claim.json`.
- `fixtures/grounded_research_briefs/invalid_artifact_backed_claim_without_artifact.json`.

## Boundary restatement
This task does NOT add web/search/provider integration. The schema validates
manually supplied research context only. All public posting remains manual.
Artifact-backed Capital Chronicle content remains blocked until real approved
alpha artifacts exist.
