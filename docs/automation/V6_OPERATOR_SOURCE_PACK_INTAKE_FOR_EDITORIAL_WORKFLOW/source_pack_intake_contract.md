# Operator Source Pack Intake Contract

## Purpose

This contract validates operator source-pack metadata and evidence presence, linking the source pack to an editorial workflow packet.

## Limit of Scope

- Validates metadata and evidence presence only.
- Does not verify or generate citations.
- Does not fetch URLs or read source locator files.
- Does not approve articles or enable publication, variants, outbox, or dispatch.
- Source truth remains pending future human/editorial verification.

## Eligibility

The source-pack manifest must align with the target `editorial_workflow_id`. The editorial workflow packet must be valid and ready for review.

## Required Top-Level Manifest Fields

- `schema_version`
- `source_pack_id`
- `operator_id`
- `created_at_manual`
- `source_pack_purpose`
- `editorial_workflow_id`
- `sources`

## Required Source Fields

- `source_id`
- `source_type`
- `title`
- `locator`
- `provided_by_operator` (must be true)
- `evidence_role`
- `notes`

## Prohibited Claims

Source packs must not claim citations are verified/generated, claim article approval/publication readiness, or contain fake public URLs, fake metrics, fake comments, or fake readiness.

## Hard State Rules

Output packets always keep:

- `source_pack_intake_available: true` (only when valid)
- `source_grounding_available_for_editorial_review: true` (only when valid)
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