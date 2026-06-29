# Local Dispatch Payload Preparation Contract

## Purpose

This contract consumes a valid operator dispatch review decision packet, active outbox entry JSON files, and active outbox payload markdown files, then validates safety states and writes local dispatch-preparation payload files for supervised review.

## Limit of Scope

- Creates local prepared dispatch payload files only.
- This is not live dispatch approval.
- This is not publication approval.
- Does not call Discord/Substack/platform APIs or webhooks.
- No destination/account binding is created yet.
- Future supervised dispatch gates remain separate and must revalidate exact hashes and destination binding.

## Eligibility Revalidation Rules

- Decision packet task_label must match `TASK_CONTENTOPS_V6_OPERATOR_DISPATCH_REVIEW_DECISION_FROM_PREFLIGHT_V0`.
- Path matching: reviewed entry and payload paths lists must match decision packet lists exactly (order-preserving and duplicate-proof).
- Inputs must not contain secret markers, fake claims, or financial advice.

## Hard State Rules

Output manifest and prepared payload files always keep:

- `local_dispatch_payload_prepared: true` (only when valid)
- `dispatch_payload_created: true` (only for local prepared files)
- `preparation_status: local_dispatch_payload_pending_supervised_dispatch_gate`
- `dispatch_execution_payload_created: false`
- `live_send_request_created: false`
- `approval_for_live_dispatch: false`
- `dispatch_allowed: false`
- `approval_for_publication: false`
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