# TASK_CONTENTOPS_0062_LOCAL_GROUNDED_EDITORIAL_PACKET_EXPORT_V0

## Title & scope
Local-only grounded editorial packet export (v0). Packages the full offline
editorial pipeline (grounded research context, SEO metadata, prompt injection
packet, citation guardrail, editorial QA, preview variants, selection packet)
into a single deterministic operator-facing export artifact that is explicitly
NOT PUBLIC POSTABLE.

## Project intent guardrails
This repo is a local-first ContentOps control-plane sidecar. It is not a live
posting engine. It prepares safe offline editorial/research packets for later
human review. Grounded search is research context only, not authority,
approval, execution, publishing power, or market truth.

## What this task built
- `live_contentops/editorial_packet_export.py`
  - `build_export_packet(req)` composes all pipeline modules from one local
    fixture input into a complete export packet.
  - `validate_export_packet(packet)` local validation that blocks/warns on
    authority grants, missing no_public_post reasons, BLOCKED-guardrail +
    publishable conflicts, missing sources/limitations, source-less
    current-event claims, prompt packets that allow live calls, and selection
    auto-selection/approval.
  - `to_json_dict(packet)` and `render_markdown_report(packet)` deterministic
    export formats.
  - `build_summary()` powers the CLI summary command.
- `tests/fixtures/editorial/export_packet_input.json` deterministic synthetic
  fixture input. All synthetic; not public postable.
- `tests/test_editorial_packet_export.py` 16 tests.
- `live_contentops/cli.py` new `grounded-editorial-packet-summary` command.
- `live_contentops/status.py` next-task pointer advanced to 0063.

## Export packet contents
- export_packet_id, source_fixture_id, content_type, target_platforms,
  audience_modes, style_modes
- grounded_research_context, seo_metadata_pack, prompt_packet,
  citation_guardrail_result, editorial_qa_result, preview_variants,
  selection_packet
- no_public_post_status, operator_review, audit_flags
- advisory_only=true, approval_granted=false, publish_ready=false,
  provider_call_allowed=false, search_call_allowed=false,
  platform_action_allowed=false, human_review_required=true

## Operator review placeholders (no authority granted)
- operator_selected_preview_id: null
- selected_by_operator: false
- operator_notes: ""
- review_status: PENDING_MANUAL_REVIEW
- approval_status: NOT_APPROVED
- publish_status: NOT_PUBLIC_POSTABLE

## Markdown report banners (always visible)
LOCAL ONLY | ADVISORY ONLY | NOT PUBLIC POSTABLE | NO PROVIDER CALL |
NO SEARCH CALL | NO PLATFORM ACTION | HUMAN REVIEW REQUIRED

## Verification
- `python -m pytest -q` -> 159 passed.
- `python -m pytest -q tests/test_editorial_packet_export.py` -> 16 passed.
- `python -m live_contentops.cli grounded-editorial-packet-summary` ->
  advisory_only/local_only true; provider/search/platform false;
  human_review_required true; approval_granted/publish_ready false.

## Risks / warnings
- All preview bodies are simulated demo content marked
  `[SIMULATED PREVIEW]` and carry a not_public_postable_reason.
- No network/provider/LLM/search/platform/credential/scheduling/posting/DM/
  browser capability was introduced.
- Citation guardrail BLOCKED status is surfaced in audit_flags and markdown
  and cannot be hidden by the export.

## Open items
- None blocking. The `.gitignore` working-tree change predates this task and
  was left untouched (outside edit scope).

## Suggested next steps
- TASK_CONTENTOPS_0063_LOCAL_GROUNDED_PACKET_AUDIT_AND_OPERATOR_REVIEW_QUEUE_V0
