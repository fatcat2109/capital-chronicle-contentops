# Operator Active Outbox Review Decision Contract

## Purpose

This contract consumes a valid active outbox eligibility packet and operator review decision JSON, then validates safety states and emits a local active-outbox creation approval-intent packet.

## Limit of Scope

- Records operator intent to allow the next local active-outbox creation step.
- This is not active outbox creation.
- This is not dispatch approval.
- This is not publication approval.
- Does not call Discord/Substack/platform APIs or webhooks.
- Future active outbox creation and dispatch gates remain separate and must revalidate exact hashes.

## Eligibility Revalidation Rules

- Eligibility task_label must match `TASK_CONTENTOPS_V6_ACTIVE_OUTBOX_ELIGIBILITY_GATE_FROM_LOCAL_PACKAGE_STAGING_V0`.
- Path matching: operator reviewed files list must equal eligibility eligible_staged_payload_files list exactly (order-preserving and duplicate-proof).
- Decision must be exactly one of: `approve_active_outbox_creation`, `reject`, `defer`.
- If `approve_active_outbox_creation`:
  - `approval_phrase` must match exactly `APPROVE_LOCAL_ACTIVE_OUTBOX_CREATION_ONLY_NOT_DISPATCH`.
  - `approval_scope` must match exactly `active_outbox_creation_only`.
- Operator decision JSON must not contain secret markers, fake claims, or financial advice.

## Hard State Rules

Output packets always keep:

- `active_outbox_creation_decision_available: true` (only when valid)
- `active_outbox_creation_approved: true` (only when approved)
- `active_outbox_entry_created: false`
- `approval_for_outbox_creation: true` (only when approved, as intent)
- `approval_for_dispatch: false`
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