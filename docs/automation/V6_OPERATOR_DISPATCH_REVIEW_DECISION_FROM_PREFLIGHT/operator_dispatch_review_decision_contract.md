# Operator Dispatch Review Decision Contract

## Purpose

This contract consumes a valid local dispatch preflight packet and operator dispatch decision JSON, then validates safety states and emits a local dispatch approval-intent packet.

## Limit of Scope

- Records operator intent to allow the next local dispatch-payload preparation step.
- This is not dispatch payload creation.
- This is not dispatch approval for live send.
- This is not publication approval.
- Does not call Discord/Substack/platform APIs or webhooks.
- Future dispatch-payload preparation and live/supervised dispatch gates remain separate and must revalidate exact hashes.

## Eligibility Revalidation Rules

- Preflight task_label must match `TASK_CONTENTOPS_V6_LOCAL_DISPATCH_PREFLIGHT_FROM_ACTIVE_OUTBOX_V0`.
- Path matching: reviewed entry and payload paths lists must match preflight lists exactly (order-preserving and duplicate-proof).
- Decision must be exactly one of: `approve_dispatch_payload_preparation`, `reject`, `defer`.
- If `approve_dispatch_payload_preparation`:
  - `approval_phrase` must match exactly `APPROVE_LOCAL_DISPATCH_PAYLOAD_PREPARATION_ONLY_NOT_SEND`.
  - `approval_scope` must match exactly `dispatch_payload_preparation_only`.
- Operator decision JSON must not contain secret markers, fake claims, or financial advice.

## Hard State Rules

Output packets always keep:

- `dispatch_review_decision_available: true` (only when valid)
- `dispatch_payload_preparation_approved: true` (only when approved)
- `approval_for_dispatch: true` (only when approved, as intent for the next step)
- `dispatch_payload_created: false`
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