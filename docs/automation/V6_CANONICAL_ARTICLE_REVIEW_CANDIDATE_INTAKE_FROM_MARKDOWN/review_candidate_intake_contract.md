# Review Candidate Intake Contract

## Purpose

Parse operator-provided Markdown drafts into local review-candidate packets.

## Input

- Explicit `.md` file path, or
- Directory path containing `.md` files.

Directory intake is deterministic and sorted by path. Non-Markdown files are blocked or ignored depending on whether passed directly or discovered during directory intake.

## Required Output Fields

Each packet includes:

- `canonical_article_review_candidate_available`
- `approved_canonical_article_available`
- `human_review_required`
- `publication_ready`
- `dispatch_allowed`
- `platform_variant_generation_allowed`
- `outbox_creation_allowed`
- `public_url`
- `public_metrics`
- `review_only`
- `kill_switch_active`
- `redaction_applied`
- `redaction_reason`

## State Rules

- `canonical_article_review_candidate_available` is `true` only for non-blocked review candidates.
- `approved_canonical_article_available` is always `false`.
- `human_review_required` is always `true`.
- `publication_ready` is always `false`.
- `dispatch_allowed` is always `false`.
- `platform_variant_generation_allowed` is always `false`.
- `outbox_creation_allowed` is always `false`.
- `public_url` is always `null`.
- `public_metrics` is always `null`.
- `review_only` is always `true`.
- `kill_switch_active` is always `true`.

## Redaction Policy

If a secret-like marker appears anywhere in metadata or body:

- `body_markdown` is replaced with `[REDACTED_SECRET_MARKER_DETECTED]`.
- `body_text` is replaced with `[REDACTED_SECRET_MARKER_DETECTED]`.
- `detected_frontmatter` keeps only keys with redacted sentinel values.
- `validation_warnings` includes `redaction_applied_secret_marker_detected`.
- `blockers` use sanitized labels only.
- `redaction_applied` is `true`.
- `redaction_reason` is `secret_marker_detected`.

`write_intake_packets()` serializes the already-redacted candidate object and must not write raw secret-bearing body or metadata values.

## Hash Policy

`source_file_sha256` is computed from raw file bytes before Markdown decoding. Parsing then decodes as UTF-8-SIG for BOM tolerance.

## Blockers

Intake blocks or fails closed for:

- Non-Markdown extension.
- Empty Markdown.
- Missing H1 title.
- Raw secret markers in metadata or body.
- Approval/public-ready/dispatch/outbox/variant claims.
- Trading advice, signal-service, position sizing, entry/exit, target, or guaranteed prediction language.

## Prohibited Artifacts

This lane never creates:

- Approved canonical article records.
- Public-ready records.
- Outbox entries.
- Platform variants.
- Dispatch records.
- Public URLs.
- Metrics.
- Comments.
- Citations.
- Fake article truth.

## Runtime Boundary

No env/provider/browser/network/API/webhook/scraping behavior is allowed.

## Final HEAD Note

No final HEAD is hardcoded in committed docs. Final HEAD belongs in external worker evidence packet only.
