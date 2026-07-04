# TASK_CONTENTOPS_0067_LOCAL_PACKET_DASHBOARD_EXPORT_AND_OPERATOR_HANDOFF_V0

## Title & scope
Local-only packet dashboard export and operator handoff (v0). Exports a
deterministic, readable handoff/report bundle from the packet registry query
and operator dashboard layers: packet counts, highest-priority items, blockers,
review status, decision history, ledger lineage, and next-operator-action
placeholders. Advisory-only, NOT PUBLIC POSTABLE.

## Project intent guardrails
Local-first ContentOps control-plane sidecar. Not a live posting engine.
Grounded search is research context only, not authority, approval, execution,
publishing power, or market truth.

## What this task built
- `live_contentops/dashboard_handoff.py`
  - `build_handoff_export(...)` deterministic handoff bundle.
  - `render_markdown_report(...)` markdown report with mandatory banners.
  - `validate_handoff_export(...)` guardrail validation.
  - `build_summary()` CLI summary.
- `tests/test_dashboard_handoff.py` (13 tests).
- `live_contentops/cli.py` new `packet-dashboard-handoff-summary` command.
- `live_contentops/status.py` next-task pointer advanced to 0068.

Note: no new fixture file was required. The fixture-backed nonzero demo path is
built in tests from the existing `packet_registry_input.json` plus an inline
source-less current-event BLOCKED packet.

## Handoff export contract
handoff_id, generated_at, dashboard_summary, registry_query_summary,
highest_priority_items, blocker_summary, warning_summary, review_status_summary,
decision_history_summary, ledger_event_summary, next_operator_action_placeholders,
safety_posture, export_formats_supported, advisory_only=true, local_only=true,
human_review_required=true, approval_granted=false, publish_ready=false,
provider_call_allowed=false, search_call_allowed=false,
platform_action_allowed=false, all_fixture_outputs_not_public_postable=true.

## Next-operator-action placeholders (local manual-review only)
REVIEW_BLOCKERS, REQUEST_REVISION, HOLD_FOR_REAL_ARTIFACT,
ACCEPT_FOR_INTERNAL_REVIEW_ONLY, ACCEPT_FOR_MANUAL_EXPORT_PACKET_ONLY. None grant
publish authority.

## Export validation (block/warn)
Zero required components; demo path with no registry records or ledger entries;
hidden BLOCKED audit/citation status; dropped blockers/warnings; hidden
source/limitation/citation issues; manual export acceptance treated as public
approval; approval_granted=true or publish_ready=true; any provider/search/
platform action; missing no_public_post_reason for fixture/demo content.

## Markdown handoff banners (always visible)
LOCAL ONLY | ADVISORY ONLY | OPERATOR HANDOFF | PACKET DASHBOARD EXPORT |
HUMAN REVIEW REQUIRED | NOT PUBLIC POSTABLE | NO PROVIDER CALL | NO SEARCH CALL |
NO PLATFORM ACTION. Sections: Executive Summary, Current Safety Posture, Counts,
Highest-Priority Packets, Blockers and Warnings, Review/Decision History,
Ledger Lineage, Next Operator Actions, Non-Publishing Boundary.

## Verification
- `python -m pytest -q` -> 243 passed.
- `python -m pytest -q tests/test_dashboard_handoff.py` -> 13 passed.
- `python -m live_contentops.cli packet-dashboard-handoff-summary` ->
  handoff_export_enabled/machine_readable_export_enabled/markdown_report_enabled/
  human_review_required true; approval_granted/publish_ready/provider/search/
  platform false; all_fixture_outputs_not_public_postable true.
- Fixture-backed demo confirmed nonzero: 2 registry records, 15 ledger entries,
  BLOCKED surfaced first in highest-priority ordering.

## Risks / warnings
- Handoff export is advisory and read-only; every ledger entry carries
  publish_status=NOT_PUBLIC_POSTABLE and publish_ready stays false.
- A BLOCKED citation/audit status cannot be hidden; validation blocks any
  attempt to undercount it.
- No network/provider/LLM/search/platform/credential/scheduling/posting/DM/
  browser capability was introduced.

## Open items
- None blocking. The `.gitignore` working-tree change is operator-owned, was
  not staged/committed/touched.

## Suggested next steps
- TASK_CONTENTOPS_0068_LOCAL_REVIEW_PACKET_BUNDLE_MANIFEST_AND_PROJECT_SOURCE_EXPORT_V0
