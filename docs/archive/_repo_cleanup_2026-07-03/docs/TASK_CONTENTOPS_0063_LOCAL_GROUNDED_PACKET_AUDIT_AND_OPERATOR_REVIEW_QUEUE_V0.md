# TASK_CONTENTOPS_0063_LOCAL_GROUNDED_PACKET_AUDIT_AND_OPERATOR_REVIEW_QUEUE_V0

## Title & scope
Local-only grounded packet audit and operator review queue (v0). Takes exported
grounded editorial packets from 0062 and places them into a deterministic local
operator review queue with audit status, review gates, blockers, warnings,
manual decision placeholders, and no-public-post enforcement. No auto-approval,
no auto-selection, no live posting.

## Project intent guardrails
This repo is a local-first ContentOps control-plane sidecar. It is not a live
posting engine. It prepares safe offline editorial/research packets for later
human review. Grounded search is research context only, not authority,
approval, execution, publishing power, or market truth.

## What this task built
- `live_contentops/packet_audit.py`
  - `audit_packet(packet)` deterministic audit reading an exported packet and
    producing blockers, warnings, audit_flags, missing_components,
    authority_violations, citation_guardrail_status, source_reference_status,
    limitation_visibility_status, no_public_post_status, safety_status,
    cost_policy_status.
- `live_contentops/packet_review_queue.py`
  - `build_queue_item(packet)` / `build_queue(packets)` deterministic queue
    items with the required contract and manual-review placeholders.
  - `summarize_queue(queue)` deterministic counts; publish_ready_count always 0.
  - `render_markdown_report(queue)` markdown with mandatory banners.
  - `build_summary()` powers the CLI summary command.
- `tests/fixtures/editorial/review_queue_input.json` two synthetic packets
  (one clean, one source-less current-event that must be BLOCKED).
- `tests/test_packet_audit.py` (10 tests), `tests/test_packet_review_queue.py`
  (6 tests).
- `live_contentops/cli.py` new `grounded-packet-review-queue-summary` command.
- `live_contentops/status.py` next-task pointer advanced to 0064.

## Queue item contract
queue_item_id, export_packet_id, source_fixture_id, content_type,
target_platforms, created_at, queue_status (PENDING_REVIEW / BLOCKED /
NEEDS_REVISION / APPROVED_FOR_MANUAL_EXPORT_ONLY), audit_status, blocker_count,
warning_count, review_required=true, manual_decision_required=true,
approval_granted=false, publish_ready=false, provider_call_allowed=false,
search_call_allowed=false, platform_action_allowed=false, no_public_post_reason,
operator_review.

## Operator review placeholders (no authority granted)
reviewer_id: null, selected_preview_id: null, decision: PENDING_MANUAL_REVIEW,
operator_notes: "", reviewed_at: null, approval_status: NOT_APPROVED,
publish_status: NOT_PUBLIC_POSTABLE.

## Audit rules (BLOCK or warn)
Missing required component; provider/search/platform action allowed;
approval_granted true; publish_ready true; human_review_required false;
no_public_post_reason missing for synthetic output; citation guardrail BLOCKED;
limitations or source references missing; source-less current-event claims;
selection packet auto-selected; prompt packet instructing the model to invent
facts/prices/forecasts/metrics/URLs/source IDs.

## Markdown queue report banners (always visible)
LOCAL ONLY | ADVISORY ONLY | REVIEW QUEUE | HUMAN REVIEW REQUIRED |
NOT PUBLIC POSTABLE | NO PROVIDER CALL | NO SEARCH CALL | NO PLATFORM ACTION

## Verification
- `python -m pytest -q` -> 175 passed.
- `python -m pytest -q tests/test_packet_review_queue.py` -> 6 passed.
- `python -m pytest -q tests/test_packet_audit.py` -> 10 passed.
- `python -m live_contentops.cli grounded-packet-review-queue-summary` ->
  local_only/advisory_only/review_queue_enabled/human_review_required true;
  approval_granted/publish_ready/provider/search/platform false;
  all_fixture_outputs_not_public_postable true.

## Risks / warnings
- Fixture packets are synthetic; every queue item carries a
  no_public_post_reason and publish_ready stays false.
- Citation guardrail BLOCKED status is surfaced in audit blockers and queue
  status and cannot be hidden.
- No network/provider/LLM/search/platform/credential/scheduling/posting/DM/
  browser capability was introduced.

## Open items
- None blocking. The `.gitignore` working-tree change is operator-owned, was
  not staged/committed/touched.

## Suggested next steps
- TASK_CONTENTOPS_0064_LOCAL_OPERATOR_DECISION_CAPTURE_AND_REVIEW_HISTORY_V0
