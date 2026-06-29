# Active Outbox Eligibility Gate Contract

## Purpose

This contract consumes a valid local outbox package staging manifest and staged preview files, then revalidates safety states and emits an eligibility review packet.

## Limit of Scope

- Produces an operator outbox review eligibility packet only.
- This is not active outbox creation.
- This is not publication approval.
- This is not dispatch approval.
- Does not call Discord/Substack/platform APIs or webhooks.
- Future active outbox creation and dispatch gates remain separate and must revalidate exact hashes.

## Eligibility Validation Rules

- Manifest task_label must match `TASK_CONTENTOPS_V6_LOCAL_OUTBOX_PACKAGE_STAGING_FROM_PAYLOAD_REVIEW_LEDGER_V0`.
- Outbox package must be staged and in preview-only mode.
- Path matching: supplied file paths list must equal normalized manifest staged_payload_files list exactly (order-preserving and duplicate-proof).
- Recomputed SHA256 over normalized UTF-8 contents must match manifest staged_payload_file_hashes.
- Staged files must contain local-only warnings.
- Files must not contain secret markers, fake claims, or financial advice.

## Hard State Rules

Output packets always keep:

- `active_outbox_eligibility_available: true` (only when valid)
- `eligible_for_operator_outbox_review: true` (only when valid)
- `active_outbox_entry_created: false`
- `approval_for_dispatch: false`
- `approval_for_outbox_creation: false`
- `approval_for_publication: false`
- `approved_canonical_article_available: false`
- `publication_ready: false`
- `dispatch_allowed: false`
- `platform_variant_generation_allowed: false`
- `outbox_creation_allowed: false`
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