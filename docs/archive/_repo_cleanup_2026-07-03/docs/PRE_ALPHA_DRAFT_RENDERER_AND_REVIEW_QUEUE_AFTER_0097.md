# Pre-Alpha Draft Renderer and Review Queue (After 0097)

Local-only, deterministic, design-only. This layer connects the 0095 content
engine outputs with the 0096 prompt pack / style profile / editorial rubric layer
and emits review-ready draft packets plus review queue items for future MANUAL
human review.

It performs no LLM/provider/search/network/credential/platform access. It posts
nothing. It reads no `.env`. It does not invent content: draft bodies come only
from the editorial packet's own draft candidates, which the 0095 engine built
deterministically from operator/fixture seeds.

## What this adds

- `schemas/pre_alpha_rendered_draft_packet.schema.json`
- `schemas/pre_alpha_review_queue_item.schema.json`
- `live_contentops/pre_alpha_draft_renderer.py`
- Safe/unsafe fixtures under `fixtures/pre_alpha_draft_renderer/`
- `tests/test_pre_alpha_draft_renderer.py`
- CLI: `python -m live_contentops.cli pre-alpha-draft-renderer-summary`

## Integration contract

`render_review_packet(editorial_packet, prompt_pack, style_profile,
editorial_rubric)` accepts:

- a 0095 editorial packet that must be valid, passing (`guardrail_status=="pass"`),
  review-required, manual-publish-only, non-publishing, non-live, and must not
  allow forecast readiness; and
- 0096 config objects (prompt pack, style profile, editorial rubric) that must
  all be present and validate via the 0096 validators.

If any precondition fails the packet is emitted with `guardrail_status="blocked"`,
`blocked_reasons` populated, and NO review queue items (fail closed). Safety flags
are always pinned regardless of input.

## Rendered draft packet

Includes `rendered_packet_id`, `source_editorial_packet_id`, `source_seed_id`,
`prompt_pack_id`, `style_profile_id`, `editorial_rubric_id`, `content_type`,
`draft_candidates[]`, `review_queue_items[]`, `guardrail_status`,
`blocked_reasons[]`, and the pinned posture: `manual_review_required=true`,
`public_postable=false`, `platform_publish_allowed_now=false`,
`live_execution_allowed_now=false`, `provider_call_made=false`,
`network_call_made=false`.

## Review queue item

Each item carries `review_queue_item_id`, `rendered_packet_id`, `draft_id`,
`platform_family`, `content_type`, `title_or_hook`, `body`, `limitations[]`,
`source_artifact_ids[]`, `is_general_process_content`, `review_status`
(`needs_manual_review` / `blocked`), and the pinned flags `reviewer_required=true`,
`publish_allowed_now=false`, `manual_publish_only=true`,
`approval_required_for_future_publish=true`, plus `guardrail_findings[]`.

## Render-time guardrails

The renderer independently re-scans each draft candidate (forbidden language,
alpha implication, unverified numeric market claim, public-postable / manual-review
flags, allowed platform family and content type) and mirrors the 0095
`validate_draft_candidate` verdict. If any rendered draft is blocked, the whole
packet is failed closed and no review queue items are exposed. This prevents an
externally supplied or tampered packet from smuggling unsafe content into the
review queue.

## Posture

No model is called, nothing is fetched, nothing is posted. All output remains
manual-review-required and not public postable. Live execution and provider calls
remain disabled.
