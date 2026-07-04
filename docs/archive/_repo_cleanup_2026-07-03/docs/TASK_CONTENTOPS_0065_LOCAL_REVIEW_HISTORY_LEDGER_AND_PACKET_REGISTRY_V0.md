# TASK_CONTENTOPS_0065_LOCAL_REVIEW_HISTORY_LEDGER_AND_PACKET_REGISTRY_V0

## Title & scope
Local-only review history ledger and packet registry (v0). Indexes exported
packets, review queue items, audits, operator decisions, and review histories
into deterministic local registry records and an append-only-style review
ledger. Makes the offline workflow traceable WITHOUT granting publishing
authority.

## Project intent guardrails
Local-first ContentOps control-plane sidecar. Not a live posting engine. Grounded
search is research context only, not authority, approval, execution, publishing
power, or market truth.

## What this task built
- `live_contentops/packet_registry.py`
  - `build_registry_record(packet, queue_item, history)` deterministic record.
  - `validate_registry_record(record)` local validation.
- `live_contentops/review_ledger.py`
  - `build_ledger_entry(...)`, `build_ledger(...)` deterministic lifecycle ledger.
  - `validate_ledger(...)`, `summarize_registry(...)`,
    `render_markdown_report(...)`, `build_summary()`.
- `tests/fixtures/editorial/packet_registry_input.json` synthetic packet with
  decisions.
- `tests/test_packet_registry.py` (7 tests), `tests/test_review_ledger.py`
  (10 tests).
- `live_contentops/cli.py` new `review-ledger-registry-summary` command.
- `live_contentops/status.py` next-task pointer advanced to 0066.

## Registry record contract
registry_record_id, export_packet_id, queue_item_id, history_id,
source_fixture_id, content_type, target_platforms, packet_status, queue_status,
latest_decision_status, audit_status, created_at, updated_at,
no_public_post_reason, advisory_only=true, approval_granted=false,
publish_ready=false, provider_call_allowed=false, search_call_allowed=false,
platform_action_allowed=false.

## Ledger entry contract
ledger_entry_id, registry_record_id, export_packet_id, queue_item_id, history_id,
event_type, event_timestamp, event_source, event_summary, blocker_count,
warning_count, decision_type, decision_status,
publish_status=NOT_PUBLIC_POSTABLE, approval_granted=false, publish_ready=false,
authority_boundary_note.

## Supported event types
PACKET_EXPORTED, AUDIT_COMPLETED, QUEUE_ITEM_CREATED,
OPERATOR_DECISION_RECORDED, REVIEW_HISTORY_UPDATED, REGISTRY_RECORD_UPDATED,
BLOCKER_DETECTED, REVISION_REQUESTED, HELD_FOR_REAL_ARTIFACT,
INTERNAL_REVIEW_ACCEPTED, MANUAL_EXPORT_PACKET_ACCEPTED.

`MANUAL_EXPORT_PACKET_ACCEPTED` is NOT public approval. It keeps
approval_granted=false, publish_ready=false, platform_action_allowed=false, and
not-public-postable status intact.

## Validation rules (block/warn)
Registry record lacking export_packet_id/queue_item_id/history_id; ledger entry
referencing unknown registry record; ledger event granting public approval or
publish_ready; contradicting statuses; hidden BLOCKED audit/citation status;
missing no_public_post_reason; manual export acceptance treated as public
approval; hidden source/limitation problems.

## Markdown report banners (always visible)
LOCAL ONLY | ADVISORY ONLY | PACKET REGISTRY | REVIEW LEDGER |
HUMAN REVIEW REQUIRED | NOT PUBLIC POSTABLE | NO PROVIDER CALL |
NO SEARCH CALL | NO PLATFORM ACTION

## Verification
- `python -m pytest -q` -> 210 passed.
- `python -m pytest -q tests/test_packet_registry.py` -> 7 passed.
- `python -m pytest -q tests/test_review_ledger.py` -> 10 passed.
- `python -m live_contentops.cli review-ledger-registry-summary` ->
  packet_registry_enabled/review_ledger_enabled/human_review_required true;
  approval_granted/publish_ready/provider/search/platform false;
  all_fixture_outputs_not_public_postable true.

## Risks / warnings
- Registry/ledger fixtures are synthetic; every record/entry carries
  not-public-postable status and publish_ready stays false.
- A BLOCKED audit/citation status cannot be hidden behind an accepted status.
- No network/provider/LLM/search/platform/credential/scheduling/posting/DM/
  browser capability was introduced.

## Open items
- None blocking. The `.gitignore` working-tree change is operator-owned, was
  not staged/committed/touched.

## Suggested next steps
- TASK_CONTENTOPS_0066_LOCAL_PACKET_REGISTRY_QUERY_AND_OPERATOR_DASHBOARD_SUMMARY_V0
