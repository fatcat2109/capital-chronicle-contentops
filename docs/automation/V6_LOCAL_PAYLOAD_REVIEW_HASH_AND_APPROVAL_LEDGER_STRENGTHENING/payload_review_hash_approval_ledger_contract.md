# Local Payload Review/Hash and Approval Ledger Contract

## Purpose

This contract records operator approval-intent for payload reviews and computes deterministic hashes of local preview files.

## Limit of Scope

- Records local payload-review hash intent only.
- It is not publication approval.
- It is not outbox approval.
- It is not dispatch approval.
- It does not create active payloads, outbox entries, webhook calls, or live-send artifacts.
- Future outbox and dispatch gates remain separate and must revalidate exact hashes.

## Approval Intent Validation Rules

- `variant_preview_staging_id` must match staging packet.
- `reviewed_preview_files` must exactly match preview files list (after path normalization).
- `approval_phrase` must equal exactly: `REVIEWED_LOCAL_PREVIEWS_ONLY_NOT_APPROVED_FOR_DISPATCH`.
- `approval_scope` must equal exactly: `payload_review_hash_only`.
- `notes` is required string, may be empty.
- Intent packet must not contain secret markers, fake claims, or financial advice.

## Hashing Rules

- Computes SHA256 over normalized UTF-8 contents of preview markdown files.
- Computes `variant_preview_staging_sha256` from canonical JSON of the staging packet if no secrets are present.
- Computes `combined_payload_hash` over staging ID, preview paths, preview hashes, intent ID, phrase, and scope.
- Do not compute or persist hashes from secret-bearing inputs.

## Hard State Rules

Output packets always keep:

- `payload_review_hash_available: true` (only when valid)
- `approval_intent_recorded: true` (only when valid)
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