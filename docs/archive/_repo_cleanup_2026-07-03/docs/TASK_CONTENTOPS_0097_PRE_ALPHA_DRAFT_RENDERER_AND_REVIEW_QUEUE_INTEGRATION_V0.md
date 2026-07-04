# TASK_CONTENTOPS_0097_PRE_ALPHA_DRAFT_RENDERER_AND_REVIEW_QUEUE_INTEGRATION_V0

## Scope

Local-only, deterministic, design-only. Builds the pre-alpha draft renderer and
review queue integration that connects 0095 content engine outputs with the 0096
prompt pack / style profile / editorial rubric layer. No LLM/provider/search/
network/credential/platform access. No posting. No `.env` reads.

## Baseline

- Starting accepted HEAD: `0931c12` on `master`.
- 0095 accepted: pre-alpha content engine + editorial packet.
- 0096 accepted: prompt pack / style profile / editorial rubric.

## Files created

- `schemas/pre_alpha_rendered_draft_packet.schema.json`
- `schemas/pre_alpha_review_queue_item.schema.json`
- `live_contentops/pre_alpha_draft_renderer.py`
- `fixtures/pre_alpha_draft_renderer/valid_render_from_build_in_public_packet.json`
- `fixtures/pre_alpha_draft_renderer/valid_render_from_macro_education_packet.json`
- `fixtures/pre_alpha_draft_renderer/invalid_public_postable_true.json`
- `fixtures/pre_alpha_draft_renderer/invalid_missing_manual_review.json`
- `fixtures/pre_alpha_draft_renderer/invalid_signal_language_render.json`
- `fixtures/pre_alpha_draft_renderer/invalid_prompt_pack_not_validated.json`
- `tests/test_pre_alpha_draft_renderer.py`
- `docs/PRE_ALPHA_DRAFT_RENDERER_AND_REVIEW_QUEUE_AFTER_0097.md`
- `docs/TASK_CONTENTOPS_0097_PRE_ALPHA_DRAFT_RENDERER_AND_REVIEW_QUEUE_INTEGRATION_V0.md`

## Files changed

- `live_contentops/cli.py`: added `pre-alpha-draft-renderer-summary` handler +
  dispatch entry. No external capability introduced.

## Renderer summary

Takes a validated, passing 0095 editorial packet plus validated 0096 prompt pack /
style profile / editorial rubric and emits a rendered draft packet with review
queue items. Draft bodies are reused from the editorial packet's own candidates;
nothing is invented. Deterministic (static timestamp; stable IDs).

## Review queue summary

One review queue item per draft candidate. Each item is `needs_manual_review`
when clean, `blocked` when guardrail findings exist. All items pin
`publish_allowed_now=false`, `manual_publish_only=true`,
`approval_required_for_future_publish=true`, `reviewer_required=true`.

## Integration with 0095 and 0096

- 0095: requires `guardrail_status=="pass"`, review-required, manual-publish-only,
  non-publishing, non-live, forecast-readiness not allowed, draft candidates
  present. Reuses `validate_draft_candidate`, `_scan_numeric_market_claim`,
  `ALLOWED_CONTENT_TYPES`, `ALLOWED_PLATFORM_FAMILIES`, `STATIC_TIMESTAMP`.
- 0096: requires prompt pack / style profile / editorial rubric all present and
  passing their 0096 validators; otherwise blocks with not-validated/invalid codes.

## Validator/guardrail behavior

- Valid build-in-public + macro-education renders pass with one review item each.
- `public_postable=true` draft blocks; review queue emptied (fail closed).
- Missing `review_required` blocks.
- Signal/financial-advice language in a draft blocks (`draft_blocked:<id>`).
- Prompt pack present but failing validation blocks (`prompt_pack_invalid`).
- Null config blocks with `*_not_validated` codes.
- Blocked packets still pin all safety flags.

## What remains disabled

LLM/provider/API/network/web/search calls; Telegram/API/live post; platform
posting; platform credentials; env/`.env` reads; fake Capital Chronicle alpha
output; public-postable content; financial advice / buy / sell / hold / signal /
execution language; scheduler / replies / DMs / scraping / metrics.

## Exact next task

`TASK_CONTENTOPS_0098_PRE_ALPHA_MANUAL_REVIEW_WORKFLOW_AND_APPROVAL_PACKET_V0`
