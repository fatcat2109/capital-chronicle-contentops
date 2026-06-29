# SEO/Editorial Metadata Proposal Contract

## Purpose

This contract consumes one valid operator source-pack intake packet and emits one structured SEO/editorial metadata proposal packet.

## Limit of Scope

- Emits structured checklists and metadata policy descriptions only.
- Does not generate final SEO metadata values (the `generated_metadata_values` field must remain empty/null).
- Does not verify or generate citations.
- Does not fetch URLs or read source locator files.
- Does not approve articles or enable publication, variants, outbox, or dispatch.
- Source truth and metadata finalization remain pending future human/editorial verification.

## Eligibility

The source-pack intake packet must be valid, available, and free of blockers or claims of publication, citations verification, or fake states.

## Required Checklists

- **SEO Review Checklist**: Defines search intent, checks title/slug/description alignment later, and requires a keyword stuffing review.
- **Editorial Metadata Checklist**: Confirms title, summary, structure, and checks for no financial advice language.
- **Source Grounding Checklist**: Requires source-pack reviews and prohibits generated citations.
- **Risk Review Checklist**: Enforces no fake URLs, fake metrics, fake claims, or trading signal/advice framing.

## Hard State Rules

Output packets always keep:

- `metadata_proposal_available: true` (only when valid)
- `generated_metadata_values: null`
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