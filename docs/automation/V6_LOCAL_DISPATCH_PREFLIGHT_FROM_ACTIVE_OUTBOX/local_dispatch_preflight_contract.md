# Local Dispatch Preflight Contract

## Purpose

This contract consumes a valid local active outbox manifest, active outbox entry JSON files, and copied payload markdown files, then validates safety states and emits a local dispatch preflight review packet.

## Limit of Scope

- Creates a local dispatch preflight review packet only.
- This is not dispatch payload creation.
- This is not dispatch approval.
- This is not publication approval.
- Does not call Discord/Substack/platform APIs or webhooks.
- Future dispatch approval and live/supervised dispatch gates remain separate and must revalidate exact hashes.

## Eligibility Revalidation Rules

- Manifest task_label must match `TASK_CONTENTOPS_V6_LOCAL_ACTIVE_OUTBOX_CREATION_FROM_OPERATOR_REVIEW_DECISION_V0`.
- Path matching: entry JSON and payload markdown files must equal manifest lists exactly (order-preserving and duplicate-proof).
- Entry JSON files must not contain secret markers, endpoint, webhook URL, token, bearer, cookie, authorization, channel ID, dispatch instruction, fake public URL/metrics/citations/readiness, or financial advice.
- Markdown payloads must contain local-only warnings.

## Hard State Rules

Output packets always keep:

- `dispatch_preflight_available: true` (only when valid)
- `eligible_for_operator_dispatch_review: true` (only when valid)
- `dispatch_payload_created: false`
- `approval_for_dispatch: false`
- `approval_for_publication: false`
- `dispatch_allowed: false`
- `platform_variant_generation_allowed: false`
- `outbox_creation_allowed: false`
- `publication_ready: false`
- `approved_canonical_article_available: false`
- `generated_citations_allowed: false`
- `citations_verified: false`
- `public_url: null`
- `public_metrics: null`
- `review_only: true`
- `human_review_required: true`
- `kill_switch_active: true`
- `runtime_truth: false`

## Runtime Boundary

Local-only and browserless. No env, provider, live API, webhook, network, scraping, dispatch, or credential validation behavior is allowed.