# Local Active Outbox Creation Contract

## Purpose

This contract consumes a valid operator active-outbox review decision packet and staged preview files, then writes local active outbox entries and copied platform payload files.

## Limit of Scope

- Creates local active outbox files only.
- This is not dispatch approval.
- This is not publication approval.
- Does not call Discord/Substack/platform APIs or webhooks.
- Future dispatch-gateway preparation and dispatch gates remain separate and must revalidate exact hashes.

## Hashing Rules

- Computes `operator_review_decision_sha256` from canonical JSON of review decision packet only if no secrets are present.
- Recomputes payload file hashes after copying and verify they match source staged hashes.
- Do not compute or persist hashes from secret-bearing inputs.

## Hard State Rules

Output packets always keep:

- `local_active_outbox_created: true` (only when valid)
- `active_outbox_entry_created: true` (only when local entries/manifest created)
- `entry_status: local_active_outbox_pending_dispatch_review`
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