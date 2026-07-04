# Local Outbox Package Staging Contract

## Purpose

This contract consumes a valid local payload review/hash approval ledger packet and staging preview files, then copies them to a staged package directory and emits an outbox staging manifest.

## Limit of Scope

- Creates local staged preview package only.
- This is not active outbox creation.
- This is not publication approval.
- This is not dispatch approval.
- Does not call Discord/Substack/platform APIs or webhooks.
- Future active outbox and dispatch gates remain separate and must revalidate exact hashes.

## Hashing Rules

- Computes `payload_review_ledger_sha256` from canonical JSON of ledger packet if no secrets are present.
- Recomputes staged file hashes and compares them to source preview hashes.
- Recomputes combined payload hash from ledger material to verify against `combined_payload_hash`.
- Do not compute or persist hashes from secret-bearing inputs.

## Hard State Rules

Output packets always keep:

- `outbox_package_staged: true` (only when valid)
- `outbox_package_preview_only: true`
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