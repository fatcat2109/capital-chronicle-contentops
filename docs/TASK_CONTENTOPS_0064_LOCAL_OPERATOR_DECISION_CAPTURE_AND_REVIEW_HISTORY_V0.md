# TASK_CONTENTOPS_0064_LOCAL_OPERATOR_DECISION_CAPTURE_AND_REVIEW_HISTORY_V0

## Title & scope
Local-only operator decision capture and review history (v0). Records
deterministic manual-review decision records for grounded packet review queue
items and preserves an append-only local review history. No decision becomes
publishing authority. Synthetic/demo/fixture content stays NOT PUBLIC POSTABLE.

## Project intent guardrails
This repo is a local-first ContentOps control-plane sidecar. It is not a live
posting engine. It prepares safe offline editorial/research packets for later
human review. Grounded search is research context only, not authority,
approval, execution, publishing power, or market truth.

## What this task built
- `live_contentops/operator_decision.py`
  - `build_decision_record(queue_item, req)` deterministic decision record.
  - `validate_decision_record(record)` local validation.
  - Allowed decision types, forbidden-intent detection.
- `live_contentops/review_history.py`
  - `build_history(queue_item, decision_records)` / `append_decision(...)`.
  - `summarize_history`, `validate_history`, `render_markdown_report`,
    `build_summary`.
- `tests/fixtures/editorial/operator_decision_input.json` synthetic decisions
  plus a forbidden decision used by negative tests.
- `tests/test_operator_decision.py` (9 tests), `tests/test_review_history.py`
  (9 tests).
- `live_contentops/cli.py` new `operator-decision-history-summary` command.
- `live_contentops/status.py` next-task pointer advanced to 0065.

## Decision record contract
decision_id, queue_item_id, export_packet_id, source_fixture_id, operator_id,
reviewer_id, decision_timestamp, decision_type, decision_status, operator_notes,
selected_preview_id, blocker_snapshot, warning_snapshot, audit_status_snapshot,
citation_guardrail_status_snapshot, decision_blockers, no_public_post_reason,
advisory_only=true, manual_decision_recorded=true, approval_granted=false,
publish_ready=false, provider_call_allowed=false, search_call_allowed=false,
platform_action_allowed=false.

## Allowed local decision types (non-publishing)
REQUEST_REVISION, REJECT_PACKET, HOLD_FOR_REAL_ARTIFACT,
ACCEPT_FOR_INTERNAL_REVIEW_ONLY, ACCEPT_FOR_MANUAL_EXPORT_PACKET_ONLY.

`ACCEPT_FOR_MANUAL_EXPORT_PACKET_ONLY` is NOT public approval. It keeps
approval_granted=false, publish_ready=false, platform_action_allowed=false, and
not-public-postable status intact.

## Forbidden decisions (blocked/downgraded to BLOCKED)
Approve public posting; set publish_ready=true; schedule; send/post/upload to a
platform; grant platform_action_allowed/provider/search authority; hide a
BLOCKED audit/citation state; override missing limitations/source references;
approve synthetic/demo/fixture content as public evidence; unknown decision type.

## Review history contract
history_id, queue_item_id, export_packet_id, decision_records, latest_decision,
revision_count, rejection_count, hold_count, internal_review_accept_count,
manual_export_packet_accept_count, current_review_status,
current_publish_status=NOT_PUBLIC_POSTABLE, approval_granted=false,
publish_ready=false, append_only_semantics_note.

## Markdown report banners (always visible)
LOCAL ONLY | ADVISORY ONLY | OPERATOR DECISION HISTORY | HUMAN REVIEW REQUIRED |
NOT PUBLIC POSTABLE | NO PROVIDER CALL | NO SEARCH CALL | NO PLATFORM ACTION

## Verification
- `python -m pytest -q` -> 193 passed.
- `python -m pytest -q tests/test_operator_decision.py` -> 9 passed.
- `python -m pytest -q tests/test_review_history.py` -> 9 passed.
- `python -m live_contentops.cli operator-decision-history-summary` ->
  local_only/advisory_only/decision_capture_enabled/review_history_enabled/
  human_review_required true; approval_granted/publish_ready/provider/search/
  platform false; all_fixture_outputs_not_public_postable true.

## Risks / warnings
- Decision/history fixtures are synthetic; every record carries a
  no_public_post_reason and publish_ready stays false.
- A decision cannot hide a BLOCKED audit/citation state nor override missing
  source/limitation problems (acceptance is downgraded to BLOCKED).
- No network/provider/LLM/search/platform/credential/scheduling/posting/DM/
  browser capability was introduced.

## Open items
- None blocking. The `.gitignore` working-tree change is operator-owned, was
  not staged/committed/touched.

## Suggested next steps
- TASK_CONTENTOPS_0065_LOCAL_REVIEW_HISTORY_LEDGER_AND_PACKET_REGISTRY_V0
