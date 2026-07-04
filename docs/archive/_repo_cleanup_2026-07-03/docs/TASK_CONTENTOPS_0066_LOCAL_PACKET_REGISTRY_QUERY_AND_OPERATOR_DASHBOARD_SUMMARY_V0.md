# TASK_CONTENTOPS_0066_LOCAL_PACKET_REGISTRY_QUERY_AND_OPERATOR_DASHBOARD_SUMMARY_V0

## Title & scope
Local-only packet registry query and operator dashboard summary (v0).
Deterministic query/filter/sort/group utilities and an operator dashboard over
the local packet registry and review ledger. Helps inspect packet status,
blockers, review state, decisions, not-public-post posture, and ledger lineage
WITHOUT granting any publishing authority.

## Project intent guardrails
Local-first ContentOps control-plane sidecar. Not a live posting engine.
Grounded search is research context only, not authority, approval, execution,
publishing power, or market truth.

## What this task built
- `live_contentops/packet_registry_query.py`
  - `build_query_items(...)`, `filter_items(...)`, `sort_items(...)`,
    `group_items(...)`, `highest_priority_items(...)`,
    `validate_query_items(...)`.
- `live_contentops/operator_dashboard.py`
  - `build_dashboard(...)`, `validate_dashboard(...)`,
    `render_markdown_report(...)`, `build_summary()`.
- `tests/test_packet_registry_query.py` (11 tests),
  `tests/test_operator_dashboard.py` (9 tests).
- `live_contentops/cli.py` new `packet-registry-dashboard-summary` command.
- `live_contentops/status.py` next-task pointer advanced to 0067.

Note: the existing `tests/fixtures/editorial/packet_registry_input.json` was
reused; no new fixture was required (a BLOCKED packet is generated inline in
tests from a source-less current-event prompt).

## Supported filters
packet_status, queue_status, latest_decision_status, audit_status, content_type,
target_platform, source_fixture_id, source_draft_id, has_blockers, has_warnings,
publish_ready, approval_granted, not_public_postable, decision_type, event_type.

## Supported groupings / sorts
status_severity (BLOCKED first, then NEEDS_REVISION, PENDING_REVIEW, held,
internal, manual-export-only), content_type, target_platform,
latest_decision_status, blocker_count descending.

## Dashboard summary fields
status, local_only, advisory_only, dashboard_enabled, registry_record_count,
ledger_entry_count, blocked_count, pending_review_count, needs_revision_count,
held_for_real_artifact_count, internal_review_accept_count,
manual_export_packet_accept_count, publish_ready_count=0,
approval_granted_count=0, no_public_post_count,
missing_source_or_limitation_issue_count, citation_guardrail_blocked_count,
provider/search/platform_action_allowed_count=0,
all_fixture_outputs_not_public_postable=true, highest_priority_items.

## Query/dashboard safety validation (block/warn)
publish_ready=true; approval/platform-action grants; provider/search grants;
hidden BLOCKED audit/citation behind accepted status; missing
no_public_post_reason; manual export acceptance treated as public approval;
ledger/query references to unknown registry records; surfaced (not hidden)
source/limitation problems.

## Markdown dashboard banners (always visible)
LOCAL ONLY | ADVISORY ONLY | OPERATOR DASHBOARD | PACKET REGISTRY QUERY |
HUMAN REVIEW REQUIRED | NOT PUBLIC POSTABLE | NO PROVIDER CALL |
NO SEARCH CALL | NO PLATFORM ACTION. Sections: Summary Counts, Highest-Priority
Items, Blockers/Warnings, Manual Decision Status, Ledger Event Summary, Next
Operator Action placeholder.

## Verification
- `python -m pytest -q` -> 230 passed.
- `python -m pytest -q tests/test_packet_registry_query.py` -> 11 passed.
- `python -m pytest -q tests/test_operator_dashboard.py` -> 9 passed.
- `python -m live_contentops.cli packet-registry-dashboard-summary` ->
  query_enabled/dashboard_enabled/human_review_required true;
  approval_granted/publish_ready/provider/search/platform false;
  all_fixture_outputs_not_public_postable true; safety_validation_enabled true.

## Risks / warnings
- Query/dashboard outputs are advisory and read-only; every item carries
  not-public-postable status and publish_ready stays false.
- A BLOCKED citation/audit status cannot be hidden behind an accepted status,
  and the dashboard validation blocks any attempt to undercount it.
- No network/provider/LLM/search/platform/credential/scheduling/posting/DM/
  browser capability was introduced.

## Open items
- None blocking. The `.gitignore` working-tree change is operator-owned, was
  not staged/committed/touched.

## Suggested next steps
- TASK_CONTENTOPS_0067_LOCAL_PACKET_DASHBOARD_EXPORT_AND_OPERATOR_HANDOFF_V0
