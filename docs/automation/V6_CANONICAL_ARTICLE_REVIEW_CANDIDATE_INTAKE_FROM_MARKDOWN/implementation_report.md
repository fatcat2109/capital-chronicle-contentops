# V6 Canonical Article Review-Candidate Intake From Markdown - Implementation Report

## Scope

Task label: `TASK_CONTENTOPS_V6_CANONICAL_ARTICLE_REVIEW_CANDIDATE_INTAKE_FROM_MARKDOWN_V0`

This implementation adds local Markdown intake for operator-provided canonical article drafts as review candidates only.

## Repair Note

Security hardening now redacts secret-marker blocked candidates before packet serialization. If secret-like markers appear in metadata or body, persisted candidate packets contain sanitized blocker labels, redacted body fields, redacted frontmatter values, `redaction_applied: true`, and `redaction_reason: "secret_marker_detected"`.

Source file hashes are computed from raw bytes before UTF-8/UTF-8-SIG decoding.

## Safety Contract

- Review candidate only.
- No approval.
- No publication readiness.
- No dispatch records.
- No outbox creation.
- No platform variant generation.
- No env reads.
- No provider calls.
- No browser sessions.
- No network/API/webhook calls.
- No scraping.
- No fake public URLs, metrics, comments, citations, or article truth.

## Files Patched

- `live_contentops/canonical_article_intake_v6.py`
- `tests/test_canonical_article_intake_v6.py`
- `docs/automation/V6_CANONICAL_ARTICLE_REVIEW_CANDIDATE_INTAKE_FROM_MARKDOWN/review_candidate_intake_contract.md`
- `docs/automation/V6_CANONICAL_ARTICLE_REVIEW_CANDIDATE_INTAKE_FROM_MARKDOWN/sample_review_candidate_packet.json`

## Final HEAD Note

No final HEAD is hardcoded in committed docs. Final HEAD belongs in external worker evidence packet only.
