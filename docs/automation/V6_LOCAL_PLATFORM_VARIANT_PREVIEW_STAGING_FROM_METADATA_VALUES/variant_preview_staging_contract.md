# Local Platform Variant Preview Staging Contract

## Purpose

This contract consumes one valid operator metadata values review packet and a canonical article draft markdown file, and emits local preview-only Substack and Discord variant markdown files and packets.

## Limit of Scope

- Emits local preview files only.
- Previews are not approved platform variants.
- Does not create outbox entries or dispatch anything.
- Does not call Discord/Substack/platform APIs or webhooks.
- Future approval/outbox/dispatch gates remain separate.

## Preview Format Rules

### Substack Preview Markdown

- Canonical title as H1 header.
- Meta description as a commented metadata block.
- Editorial summary as local summary block.
- Warning label: `LOCAL PREVIEW ONLY - NOT APPROVED FOR PUBLICATION`.
- Appends the original markdown body.

### Discord Preview Markdown

- Community drop preview derived from title and summary.
- Grounding source pack reminder.
- Warning label: `LOCAL PREVIEW ONLY - NOT APPROVED FOR DISCORD DISPATCH`.

## Hard State Rules

Output packets always keep:

- `variant_preview_staging_available: true` (only when valid)
- `variant_previews_generated: true` (only when valid)
- `preview_only: true`
- `platform_variant_generation_allowed: false`
- `outbox_creation_allowed: false`
- `dispatch_allowed: false`
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