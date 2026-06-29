# Review Decision Contract

## Purpose

This contract turns one canonical article review-candidate packet into one local human-review decision packet.

## Decision Values

Allowed values:

- `accept_for_editorial_workflow`
- `reject`
- `defer`

## Editorial Workflow Only

`accept_for_editorial_workflow` means the candidate can move to a later editorial workflow lane. It is not approval for publication.

## Hard Prohibitions

This contract does not:

- Create approved canonical articles.
- Mark anything publication-ready.
- Generate platform variants.
- Create outbox entries.
- Create dispatch records.
- Create public URLs.
- Create metrics.
- Create comments.
- Create citations.
- Invent runtime truth.

## Acceptance Rule

`accepted_for_editorial_workflow` may be `true` only when:

- `decision` is `accept_for_editorial_workflow`.
- Input candidate status is `REVIEW_CANDIDATE_PENDING_HUMAN_REVIEW`.
- Input candidate is available for review.
- Input candidate has no blockers.
- Input candidate has `redaction_applied: false`.
- Input candidate has all approval/publication/dispatch/outbox/variant states false/null.
- Input candidate has no raw secret markers in body/frontmatter/output fields.

## State Rules

Decision packets always keep:

- `approved_canonical_article_available: false`
- `human_review_required: true`
- `publication_ready: false`
- `dispatch_allowed: false`
- `platform_variant_generation_allowed: false`
- `outbox_creation_allowed: false`
- `public_url: null`
- `public_metrics: null`
- `review_only: true`
- `kill_switch_active: true`
- `runtime_truth: false`

## Safety Rules

Review notes are persisted only after secret-marker scanning. If notes contain secret-like markers, notes are replaced with `[REDACTED_SECRET_MARKER_DETECTED]`, a warning is emitted, and the decision packet is blocked.

Decision packets reference source candidate ID and deterministic candidate packet hash. They do not copy raw draft body.

## Runtime Boundary

Local-only and browserless. No env, provider, live API, webhook, network, scraping, dispatch, or credential validation behavior is allowed.
