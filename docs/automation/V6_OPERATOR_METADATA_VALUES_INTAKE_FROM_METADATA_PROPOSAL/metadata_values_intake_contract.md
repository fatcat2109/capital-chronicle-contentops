# SEO/Editorial Metadata Values Intake Contract

## Purpose

This contract ingests operator-supplied metadata values for review and validation only.

## Limit of Scope

- Does not finalize metadata.
- Does not approve articles or enable publication, variants, outbox, or dispatch.
- Does not generate or verify citations.
- Does not fetch URLs or read source locator files.
- Future finalization/approval remains separate.

## Metadata Values Validation Rules

- `canonical_title`: non-empty string, 20-120 chars.
- `canonical_slug`: non-empty lowercase hyphenated alphanumeric string, 3-90 chars, no URL.
- `meta_description`: non-empty string, 70-180 chars.
- `focus_keywords`: non-empty list of 1-10 strings, each 2-60 chars.
- `editorial_summary`: non-empty string, 30-500 chars.
- `intended_search_intent`: non-empty string, 10-300 chars.
- `notes`: required string, may be empty, must not be a non-string type. Notes are scanned for prohibited content but are not copied into the output review packet.
- `metadata_values.metadata_proposal_id` must match `metadata_proposal.metadata_proposal_id`.

## Prohibited Content

Values must not contain raw secret-like markers, fake claims of metrics/readiness, publication approval, dispatch/outbox/variant claims, or financial advice/signal-service framing.

## Hard State Rules

Output packets always keep:

- `metadata_values_available_for_editorial_review: true` (only when valid)
- `metadata_values_finalized: false`
- `generated_by_llm: false`
- `operator_supplied: true` (when valid)
- `generated_citations_allowed: false`
- `citations_verified: false`
- `approved_canonical_article_available: false`
- `publication_ready: false`
- `dispatch_allowed: false`
- `platform_variant_generation_allowed: false`
- `outbox_creation_allowed: false`
- `public_url: null`
- `public_metrics: null`
- `review_only: true`
- `human_review_required: true`
- `kill_switch_active: true`
- `runtime_truth: false`

## Runtime Boundary

Local-only and browserless. No env, provider, live API, webhook, network, scraping, dispatch, or credential validation behavior is allowed.